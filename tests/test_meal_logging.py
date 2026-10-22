"""Meal logging service tests. Synthetic data only; repository is mocked."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from bulking_app.services import meal_logging as svc

GOOD = {"item_type": "free_text", "item_name": "x", "quantity": 1, "unit": "g"}
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
        assert svc.add_entry("2026-10-11", GOOD)["id"] == 7
        assert c.call_args.kwargs["source"] == "manual"
    with patch.object(svc.meal_log, "create_log", return_value=7), \
         patch.object(svc.meal_log, "get_log", return_value=None):
        with pytest.raises(svc.LogWriteError):
            svc.add_entry("2026-10-11", GOOD)


def test_edit_missing_entry_raises():
    with patch.object(svc.meal_log, "update_log", return_value=False):
        with pytest.raises(svc.LogWriteError):
            svc.edit_entry(1, "2026-10-11", GOOD)


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


@pytest.mark.parametrize("entry", [
    {"item_name": " ", "quantity": 1, "unit": "g"},
    {"item_name": "x", "quantity": 0, "unit": "g"},
    {"item_name": "x", "quantity": -1, "unit": "g"},
    {"item_name": "x", "quantity": "abc", "unit": "g"},
    {"item_name": "x", "quantity": 1, "unit": " "},
    {"item_name": "x", "quantity": 1, "unit": "g", "calories_kcal": "abc"},
    {"item_name": "x", "quantity": 1, "unit": "g", "protein_g": "-3"},
])
def test_bad_input_never_reaches_repository(entry):
    with patch.object(svc.meal_log, "create_log") as c, patch.object(svc.meal_log, "update_log") as u:
        with pytest.raises(ValueError):
            svc.add_entry("2026-10-11", entry)
        with pytest.raises(ValueError):
            svc.edit_entry(1, "2026-10-11", entry)
        c.assert_not_called()
        u.assert_not_called()


def test_blank_nutrition_is_unknown_not_zero():
    clean = svc.validate_entry({"item_name": "x", "quantity": 1, "unit": "g",
                                "calories_kcal": "", "protein_g": " ", "nutrition_source": "estimate"})
    assert clean["calories_kcal"] is None and clean["protein_g"] is None
    assert clean["nutrition_source"] == "unknown"


def test_repository_error_becomes_log_write_error():
    with patch.object(svc.meal_log, "create_log", side_effect=Exception("db down")):
        with pytest.raises(svc.LogWriteError):
            svc.add_entry("2026-10-11", GOOD)


def test_edit_entry_success():
    with patch.object(svc.meal_log, "update_log", return_value=True) as u, \
         patch.object(svc.meal_log, "get_log", return_value={"id": 1}):
        assert svc.edit_entry(1, "2026-10-11", GOOD)["id"] == 1
        assert u.call_args.kwargs["source"] == "manual"


def test_food_entry_manual_nutrition_override():
    e = svc.food_entry({"id": 2, "food_name": "Test item"}, 1, "piece", "150", "")
    assert e["calories_kcal"] == 150 and e["protein_g"] is None
    assert e["nutrition_source"] == "user_entered"


def _calc_log():
    return {"item_type": "recipe", "recipe_id": 1, "food_id": None, "plan_meal_id": None,
            "quantity": 100.0, "unit": "g", "calories_kcal": 200.0, "protein_g": 10.0,
            "nutrition_source": "calculated"}


def test_edit_quantity_rescales_calculated_nutrition():
    e = svc.edited_entry(_calc_log(), "Test bowl", 200, "g", "200", "10")
    assert (e["calories_kcal"], e["protein_g"], e["nutrition_source"]) == (400.0, 20.0, "calculated")


def test_edit_unit_relabels_calculated_as_estimate():
    assert svc.edited_entry(_calc_log(), "Test bowl", 1, "bowl", "200", "10")["nutrition_source"] == "estimate"


def test_edit_typed_nutrition_is_user_entered():
    assert svc.edited_entry(_calc_log(), "Test bowl", 100, "g", "250", "10")["nutrition_source"] == "user_entered"


# --- typed commands: override and undo ---
_NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
_FOODS = [{"id": 1, "food_name": "Egg", "unit": "piece", "calories_kcal": None, "protein_g": None}]


def _recent_log(**kw):
    base = {"id": 7, "item_name": "egg", "quantity": 3, "unit": "piece", "source": "command",
            "created_at": _NOW}
    return {**base, **kw}


def test_command_duplicate_blocked_by_default():
    with patch.object(svc.meal_log, "list_logs", return_value=[_recent_log()]), \
            patch.object(svc.meal_log, "create_log") as create:
        res = svc.log_from_command("I ate 3 eggs", "d", _FOODS, now=_NOW)
    assert res["status"] == "duplicate"
    create.assert_not_called()


def test_command_duplicate_override_logs_again():
    with patch.object(svc.meal_log, "list_logs", return_value=[_recent_log()]), \
            patch.object(svc.meal_log, "create_log", return_value=8) as create, \
            patch.object(svc.meal_log, "get_log", return_value=_recent_log(id=8)):
        res = svc.log_from_command("I ate 3 eggs", "d", _FOODS, now=_NOW, allow_duplicate=True)
    assert res["status"] == "logged"
    create.assert_called_once()


def test_undo_message_names_entry():
    msg = svc.undo_message({"item_name": "Egg", "quantity": 3, "unit": "piece"})
    assert "Egg" in msg and "removed" in msg


def test_undo_message_when_nothing():
    assert "No typed entry" in svc.undo_message(None)


def test_undo_last_command_removes_newest_command_only():
    logs = [_recent_log(id=1), _recent_log(id=5), _recent_log(id=9, source="manual")]
    with patch.object(svc.meal_log, "list_logs", return_value=logs), \
            patch.object(svc, "remove_entry") as rm:
        undone = svc.undo_last_command("d")
    assert undone["id"] == 5
    rm.assert_called_once_with(5)
