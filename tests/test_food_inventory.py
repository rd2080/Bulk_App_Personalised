import unittest
from unittest.mock import MagicMock, patch

from bulking_app.repositories.food_inventory import add_food, set_food_availability, update_food


class FoodInventoryTests(unittest.TestCase):
    @patch("bulking_app.repositories.food_inventory.connection")
    def test_add_food_rejects_duplicate(self, connection_mock):
        conn = MagicMock()
        conn.__enter__.return_value = conn
        conn.execute.return_value.fetchone.return_value = (9,)
        connection_mock.return_value = conn

        with self.assertRaisesRegex(ValueError, "already exists"):
            add_food(food_name="Eggs", availability_type="stock_tracked", quantity=6, unit="pieces")

    @patch("bulking_app.repositories.food_inventory.connection")
    def test_add_food_returns_new_id(self, connection_mock):
        conn = MagicMock()
        conn.__enter__.return_value = conn
        conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=None)),
            MagicMock(fetchone=MagicMock(return_value=(12,))),
        ]
        connection_mock.return_value = conn

        result = add_food(food_name="Eggs", availability_type="stock_tracked", quantity=6, unit="pieces")
        self.assertEqual(result, 12)

    @patch("bulking_app.repositories.food_inventory.connection")
    def test_update_and_toggle_use_database(self, connection_mock):
        conn = MagicMock()
        conn.__enter__.return_value = conn
        update_result = MagicMock(rowcount=1)
        toggle_result = MagicMock(rowcount=1)
        conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=None)),
            update_result,
            toggle_result,
        ]
        connection_mock.return_value = conn

        update_food(food_id=4, food_name="Milk", availability_type="always_available",
                    quantity=1.5, unit="L")
        set_food_availability(food_id=4, is_available=False)
        self.assertEqual(update_result.rowcount, 1)
        self.assertEqual(toggle_result.rowcount, 1)


if __name__ == "__main__":
    unittest.main()
