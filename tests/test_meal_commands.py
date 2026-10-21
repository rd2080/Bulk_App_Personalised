import unittest
from datetime import date
from unittest.mock import patch

from bulking_app.meal_commands import parse_meal_commands, apply_meal_commands


class ParseMealCommandsTests(unittest.TestCase):
    def test_parses_multiple_meals(self):
        parsed = parse_meal_commands("Breakfast: two bananas and milk. For lunch, three rotis and paneer bhurji. Dinner will be dal rice.")
        self.assertIsNone(parsed["clarification"])
        self.assertEqual([x["meal_type"] for x in parsed["operations"]], ["Breakfast", "Lunch", "Dinner"])
        self.assertEqual(parsed["operations"][0]["content"], "two bananas and milk")
        self.assertEqual(parsed["operations"][2]["content"], "dal rice")

    def test_replace_command(self):
        parsed = parse_meal_commands("Change my lunch to three rotis and paneer bhurji.")
        self.assertEqual(parsed["operations"][0], {"action": "replace", "meal_type": "Lunch", "content": "three rotis and paneer bhurji"})

    def test_add_command(self):
        parsed = parse_meal_commands("Add a banana to breakfast.")
        self.assertEqual(parsed["operations"][0]["action"], "add")
        self.assertEqual(parsed["operations"][0]["meal_type"], "Breakfast")

    def test_remove_command(self):
        parsed = parse_meal_commands("Remove dinner.")
        self.assertEqual(parsed["operations"][0]["action"], "remove")
        self.assertEqual(parsed["operations"][0]["meal_type"], "Dinner")

    def test_ambiguous_snack_requests_clarification(self):
        parsed = parse_meal_commands("Remove snack.")
        self.assertIsNotNone(parsed["clarification"])
        self.assertEqual(parsed["operations"], [])

    def test_unlabeled_text_requests_clarification(self):
        parsed = parse_meal_commands("I want to eat paneer today.")
        self.assertIsNotNone(parsed["clarification"])

    @patch("bulking_app.meal_commands.list_meals")
    def test_multiple_existing_entries_request_clarification_without_writes(self, list_mock):
        list_mock.return_value = [
            {"id": 1, "meal_type": "Lunch", "meal_name": "Roti", "description": ""},
            {"id": 2, "meal_type": "Lunch", "meal_name": "Rice", "description": ""},
        ]
        with patch("bulking_app.meal_commands.save_meal") as save_mock:
            result = apply_meal_commands("Change lunch to dal rice", date(2026, 10, 11))
        self.assertEqual(result["status"], "clarification")
        save_mock.assert_not_called()


class SingleSlotCommandRegressionTests(unittest.TestCase):
    def test_single_slot_commands_always_include_clarification_key(self):
        for text in ("Change lunch to dal rice", "Add a banana to breakfast", "Remove dinner"):
            with self.subTest(text=text):
                parsed = parse_meal_commands(text)
                self.assertIn("clarification", parsed)
                self.assertIsNone(parsed["clarification"])

    @patch("bulking_app.meal_commands.list_meals", return_value=[])
    def test_apply_single_replace_creates_meal_when_slot_empty(self, _list_mock):
        with patch("bulking_app.meal_commands.save_meal") as save_mock:
            result = apply_meal_commands("Change lunch to dal rice", date(2026, 10, 11))
        self.assertEqual(result["status"], "success")
        save_mock.assert_called_once()

    @patch("bulking_app.meal_commands.list_meals", return_value=[])
    def test_apply_remove_on_empty_slot_changes_nothing(self, _list_mock):
        with patch("bulking_app.meal_commands.delete_meal") as delete_mock:
            result = apply_meal_commands("Remove dinner", date(2026, 10, 11))
        self.assertEqual(result["status"], "success")
        delete_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
