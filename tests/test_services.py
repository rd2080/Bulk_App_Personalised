import json
import tempfile
import unittest
from pathlib import Path

from bulking_app.database import initialize_database
from bulking_app.ai.factory import get_planner
from bulking_app.services.tools import recent_plans, save_daily_plan


class ServiceTests(unittest.TestCase):
    def test_save_plan_persists_checkin_foods_plan_and_log(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "test.db")
            initialize_database(path)
            plan_id = save_daily_plan(weight_kg=72.4, feeling="Good energy",
                foods=[{"name": "oats", "quantity": "80 g"}], notes="Gym at 5",
                plan={"summary": "A balanced day"}, provider="gemini",
                entry_date="2026-01-01", path=path)
            self.assertGreater(plan_id, 0)
            plans = recent_plans(path=path)
            self.assertEqual(plans[0]["plan"]["summary"], "A balanced day")
            import sqlite3
            with sqlite3.connect(path) as conn:
                self.assertEqual(conn.execute("SELECT weight_kg FROM weight_entries").fetchone()[0], 72.4)
                self.assertEqual(conn.execute("SELECT name FROM foods").fetchone()[0], "oats")
                self.assertEqual(conn.execute("SELECT event_type FROM logs").fetchone()[0], "plan_saved")
                checkin = json.loads(conn.execute("SELECT check_in FROM daily_plans").fetchone()[0])
                self.assertEqual(checkin["feeling"], "Good energy")

    def test_invalid_checkin_is_rejected(self):
        with self.assertRaises(ValueError):
            save_daily_plan(weight_kg=10, feeling="", foods=[], notes="", plan={}, provider="gemini")

    def test_unknown_provider_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "AI_PROVIDER"):
            get_planner("unknown")


if __name__ == "__main__":
    unittest.main()
