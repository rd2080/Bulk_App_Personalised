import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from bulking_app.repositories.meal_plan import delete_meal, list_meals, save_meal


class MealPlanTests(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.conn.__enter__.return_value = self.conn

    @patch("bulking_app.repositories.meal_plan.connection")
    def test_add_meal_creates_plan_and_appends_position(self, connection_mock):
        connection_mock.return_value = self.conn
        self.conn.execute.side_effect = [MagicMock(fetchone=MagicMock(return_value=(8,))),
                                         MagicMock(fetchone=MagicMock(return_value=(2,))),
                                         MagicMock(fetchone=MagicMock(return_value=(15,)))]
        result = save_meal(plan_date="2026-10-11", meal_type="Breakfast",
                           meal_name="  Oats  ", description="  With milk ")
        self.assertEqual(result, 15)
        self.assertEqual(self.conn.execute.call_args_list[0].args[1], (date(2026, 10, 11),))
        self.assertEqual(self.conn.execute.call_args_list[2].args[1], (8, "Breakfast", "Oats", "With milk", 2))

    @patch("bulking_app.repositories.meal_plan.connection")
    def test_update_is_limited_to_selected_plan(self, connection_mock):
        connection_mock.return_value = self.conn
        self.conn.execute.side_effect = [MagicMock(fetchone=MagicMock(return_value=(8,))),
                                         MagicMock(fetchone=MagicMock(return_value=(15,)))]
        self.assertEqual(save_meal(plan_date=date(2026, 10, 11), meal_type="Dinner",
                                   meal_name="Dal rice", meal_id=15), 15)
        self.assertIn("WHERE id = %s AND plan_id = %s", self.conn.execute.call_args.args[0])

    def test_invalid_values_do_not_open_database(self):
        with patch("bulking_app.repositories.meal_plan.connection") as connection_mock:
            with self.assertRaises(ValueError):
                save_meal(plan_date="2026-10-11", meal_type="Brunch", meal_name="Eggs")
            with self.assertRaises(ValueError):
                save_meal(plan_date="2026-10-11", meal_type="Lunch", meal_name=" ")
            connection_mock.assert_not_called()

    @patch("bulking_app.repositories.meal_plan.connection")
    def test_list_and_delete(self, connection_mock):
        connection_mock.return_value = self.conn
        self.conn.execute.return_value.fetchall.return_value = [(2, "Lunch", "Dal rice", None, 0)]
        rows = list_meals("2026-10-11")
        self.assertEqual(rows[0]["description"], "")
        self.conn.execute.return_value.fetchone.return_value = (2,)
        self.assertTrue(delete_meal(plan_date="2026-10-11", meal_id=2))


if __name__ == "__main__":
    unittest.main()
