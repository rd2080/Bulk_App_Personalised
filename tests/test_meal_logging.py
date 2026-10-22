"""Meal logging service tests. Synthetic data only; repository is mocked."""

from unittest.mock import patch

import pytest

from bulking_app.services import meal_logging as svc

RECIPE = {"id": 1, "recipe_name": "Test bowl", "total_weight_g": 400,
          "calories_kcal": 800, "protein_g": 40}


def test_recipe_partial_serving_scales_nutrition():
    e = svc.recipe_entry(RECIPE, 100)
    assert (e["calories_kcal"], e["protein_g"], e["unit"]) == (200.0, 10.0, "g")
    assert e["nutrition_source"] == "calculated"


def test_recipe_unknown_nutrition_stays_unknown():
    e = svc.recipe_entry({**RECIPE, "calories_kcal": None, "protein_g": None}, 100)
    assert "calories_kcal" not in e and "nutrition_source" not in e


def test_recipe_rejects_zero_amount():
    with pytest.raises(ValueError):
        svc.recipe_entry(RECIPE, 0)


def test_food_entry_has_no_nutrition():
    e = svc.food_entry({"id": 2, "food_name": "Test item"}, 2, "piece")
    assert e["food_id"] == 2 and "calories_kcal" not in e


def test_add_entry_confirms_only_after_read_back():
    with patch.object(svc.meal_log, "create_log", return_value=7) as c, \
         patch.object(svc.meal_log, "get_log", return_value={"id": 7}):
        assert svc.add_entry("2026-10-11", {"item_type": "free_text"})["id"] == 7
        assert c.call_args.kwargs["source"] == "manual"
    with patch.object(svc.meal_log, "create_log", return_value=7), \
         patch.object(svc.meal_log, "get_log", return_value=None):
        with pytest.raises(svc.LogWriteError):
            svc.add_entry("2026-10-11", {})


def test_edit_missing_entry_raises():
    with patch.object(svc.meal_log, "update_log", return_value=False):
        with pytest.raises(svc.LogWriteError):
            svc.edit_entry(1, "2026-10-11", {})


def test_remove_verifies_and_is_idempotent():
    with patch.object(svc.meal_log, "soft_delete_log", return_value=True), \
         patch.object(svc.meal_log, "get_log", return_value=None):
        svc.remove_entry(1)
    with patch.object(svc.meal_log, "soft_delete_log", return_value=False):
        with pytest.raises(svc.LogWriteError):
            svc.remove_entry(1)
    with patch.object(svc.meal_log, "soft_delete_log", return_value=True), \
         patch.object(svc.meal_log, "get_log", return_value={"id": 1}):
        with pytest.raises(svc.LogWriteError):
            svc.remove_entry(1)


def test_day_summary_known_totals_and_incomplete():
    logs = [{"calories_kcal": 200.0, "protein_g": 10.0},
            {"calories_kcal": None, "protein_g": None}]
    with patch.object(svc.meal_log, "list_logs", return_value=logs):
        s = svc.day_summary("2026-10-11")
    assert (s["known_kcal"], s["known_protein_g"], s["incomplete"]) == (200.0, 10.0, True)


def test_day_summary_all_unknown_is_none_not_zero():
    with patch.object(svc.meal_log, "list_logs", return_value=[{"calories_kcal": None, "protein_g": None}]):
        assert svc.day_summary("2026-10-11")["known_kcal"] is None
    assert svc.format_value(None, "kcal") == "unknown"
