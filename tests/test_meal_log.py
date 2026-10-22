"""Meal log repository tests. Synthetic data only."""

import os
import unittest
from datetime import date, time
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bulking_app.repositories import meal_log
from bulking_app.repositories.meal_log import (
    create_log, get_log, list_logs, soft_delete_log, update_log,
)

MIGRATION = Path(__file__).resolve().parents[1] / "database/migrations/009_create_meal_logs.sql"


class MealLogTests(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.conn.__enter__.return_value = self.conn
        patcher = patch("bulking_app.repositories.meal_log.connection", return_value=self.conn)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_create_without_plan_stores_null_nutrition(self):
        self.conn.execute.return_value.fetchone.return_value = (5,)
        new_id = create_log(log_date="2026-10-11", item_type="free_text",
                            item_name="  Test snack ", quantity="2", unit=" piece ")
        self.assertEqual(new_id, 5)
        sql, params = self.conn.execute.call_args.args
        self.assertIn("INSERT INTO meal_logs", sql)
        self.assertEqual(params, (date(2026, 10, 11), None, "free_text", None, None,
                                  "Test snack", Decimal("2"), "piece", None, None,
                                  "unknown", None, "manual"))

    def test_create_with_nutrition_and_plan_link(self):
        self.conn.execute.return_value.fetchone.return_value = (6,)
        create_log(log_date=date(2026, 10, 11), log_time="08:30", item_type="recipe",
                   recipe_id=3, item_name="Test shake", quantity=1.5, unit="serving",
                   calories_kcal=400, protein_g=0, nutrition_source="calculated",
                   plan_meal_id=9, source="command")
        params = self.conn.execute.call_args.args[1]
        self.assertEqual(params[1], time(8, 30))
        self.assertEqual(params[8:], (Decimal("400"), Decimal("0"), "calculated", 9, "command"))

    def test_known_zero_is_kept_but_missing_is_null(self):
        self.conn.execute.return_value.fetchone.return_value = (1,)
        create_log(log_date="2026-10-11", item_type="free_text", item_name="x",
                   quantity=1, unit="g", calories_kcal=100, protein_g=None,
                   nutrition_source="user_entered")
        params = self.conn.execute.call_args.args[1]
        self.assertEqual((params[8], params[9]), (Decimal("100"), None))

    def test_invalid_input_never_opens_database(self):
        bad = [
            dict(item_type="meal", item_name="a", quantity=1, unit="g"),
            dict(item_type="free_text", item_name=" ", quantity=1, unit="g"),
            dict(item_type="free_text", item_name="a", quantity=0, unit="g"),
            dict(item_type="free_text", item_name="a", quantity="abc", unit="g"),
            dict(item_type="free_text", item_name="a", quantity=None, unit="g"),
            dict(item_type="free_text", item_name="a", quantity=1, unit=" "),
            dict(item_type="free_text", item_name="a", quantity=1, unit="g", calories_kcal=-1,
                 nutrition_source="estimate"),
            dict(item_type="free_text", item_name="a", quantity=1, unit="g", calories_kcal=5),
            dict(item_type="free_text", item_name="a", quantity=1, unit="g", recipe_id=1),
            dict(item_type="recipe", item_name="a", quantity=1, unit="g", food_id=1),
            dict(item_type="free_text", item_name="a", quantity=1, unit="g", source="plan"),
        ]
        self.conn.reset_mock()
        for kwargs in bad:
            with self.assertRaises(ValueError, msg=kwargs):
                create_log(log_date="2026-10-11", **kwargs)
        self.conn.execute.assert_not_called()

    def test_update_is_limited_to_active_row_and_sets_updated_at(self):
        self.conn.execute.return_value.fetchone.return_value = (4,)
        self.assertTrue(update_log(4, log_date="2026-10-11", item_type="food", food_id=2,
                                   item_name="Test food", quantity=100, unit="g"))
        sql, params = self.conn.execute.call_args.args
        self.assertIn("updated_at = NOW()", sql)
        self.assertIn("deleted_at IS NULL", sql)
        self.assertEqual(params[-1], 4)

    def test_update_missing_returns_false(self):
        self.conn.execute.return_value.fetchone.return_value = None
        self.assertFalse(update_log(4, log_date="2026-10-11", item_type="free_text",
                                    item_name="a", quantity=1, unit="g"))

    def test_soft_delete_does_not_delete_rows(self):
        self.conn.execute.return_value.fetchone.return_value = (4,)
        self.assertTrue(soft_delete_log(4))
        sql = self.conn.execute.call_args.args[0]
        self.assertIn("SET deleted_at = NOW()", sql)
        self.assertNotIn("DELETE FROM", sql)
        self.conn.execute.return_value.fetchone.return_value = None
        self.assertFalse(soft_delete_log(4))

    def test_get_and_list_hide_deleted_by_default(self):
        row = (1, date(2026, 10, 11), None, "free_text", None, None, "Test", Decimal("2.00"),
               "piece", None, None, "unknown", None, "manual", None, None, None)
        self.conn.execute.return_value.fetchone.return_value = row
        self.conn.execute.return_value.fetchall.return_value = [row]
        got = get_log(1)
        self.assertIn("deleted_at IS NULL", self.conn.execute.call_args.args[0])
        self.assertIsNone(got["calories_kcal"])
        self.assertEqual(got["quantity"], 2.0)
        self.assertEqual(got["unit"], "piece")
        rows = list_logs("2026-10-11")
        self.assertEqual(len(rows), 1)
        self.assertEqual(self.conn.execute.call_args.args[1], (date(2026, 10, 11),))
        list_logs("2026-10-11", include_deleted=True)
        self.assertNotIn("deleted_at IS NULL", self.conn.execute.call_args.args[0])
        get_log(1, include_deleted=True)
        self.assertNotIn("deleted_at IS NULL", self.conn.execute.call_args.args[0])

    def test_plan_modules_do_not_reference_meal_logs(self):
        root = Path(meal_log.__file__).parent
        self.assertNotIn("meal_logs", (root / "meal_plan.py").read_text())


class MigrationTests(unittest.TestCase):
    def test_migration_is_additive_and_rerun_safe(self):
        # FK actions only ever touch meal_logs rows; strip them and comments first.
        lines = [ln for ln in MIGRATION.read_text().splitlines() if not ln.startswith("--")]
        text = "\n".join(lines).upper().replace("ON DELETE SET NULL", "")
        self.assertIn("CREATE TABLE IF NOT EXISTS MEAL_LOGS", text)
        for forbidden in ("DROP ", "DELETE ", "UPDATE ", "ALTER TABLE", "TRUNCATE"):
            self.assertNotIn(forbidden, text)


@pytest.mark.skipif(not os.getenv("SMOKE_DATABASE_URL"), reason="SMOKE_DATABASE_URL not set")
def test_roundtrip_on_throwaway_database(monkeypatch):
    url = os.environ["SMOKE_DATABASE_URL"]
    assert "neon" not in url.lower()
    monkeypatch.setenv("DATABASE_URL", url)
    new_id = create_log(log_date="2026-10-11", item_type="free_text", item_name="Test item",
                        quantity=2, unit="piece")
    row = get_log(new_id)
    assert row["calories_kcal"] is None and row["nutrition_source"] == "unknown"
    assert update_log(new_id, log_date="2026-10-11", item_type="free_text",
                      item_name="Test item", quantity=3, unit="piece",
                      calories_kcal=210, nutrition_source="user_entered")
    assert get_log(new_id)["calories_kcal"] == 210.0
    assert soft_delete_log(new_id)
    assert get_log(new_id) is None
    assert get_log(new_id, include_deleted=True)["deleted_at"] is not None
    assert all(r["id"] != new_id for r in list_logs("2026-10-11"))


if __name__ == "__main__":
    unittest.main()
