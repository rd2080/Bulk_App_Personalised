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


# --- "I ate ..." commands (synthetic data) ---
from datetime import datetime, timedelta, timezone  # noqa: E402

from bulking_app.meal_commands import parse_eaten_command  # noqa: E402
from bulking_app.services import meal_logging as svc  # noqa: E402

NOW = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)
FOODS = [{"id": 1, "food_name": "Egg"}, {"id": 2, "food_name": "Rice"}]


def _saved(**kw):
    base = {"id": 9, "item_name": "Egg", "quantity": 3.0, "unit": "piece",
            "source": "command", "created_at": NOW - timedelta(seconds=30)}
    return {**base, **kw}


def test_parse_word_count_defaults_to_piece():
    r = parse_eaten_command("I ate three eggs")
    assert (r["status"], r["item_name"], r["quantity"], r["unit"]) == ("ok", "eggs", 3.0, "piece")


def test_parse_grams():
    r = parse_eaten_command("had 200 g of rice.")
    assert (r["item_name"], r["quantity"], r["unit"]) == ("rice", 200.0, "g")


def test_parse_missing_amount_asks():
    assert parse_eaten_command("I ate eggs")["status"] == "clarification"
    assert parse_eaten_command("I ate")["status"] == "clarification"
    assert parse_eaten_command("I ate 2 eggs and rice")["status"] == "clarification"
    assert parse_eaten_command("hello")["status"] == "clarification"


def test_log_from_command_known_food_unknown_nutrition():
    with patch.object(svc.meal_log, "list_logs", return_value=[]), \
         patch.object(svc.meal_log, "create_log", return_value=9) as create, \
         patch.object(svc.meal_log, "get_log", return_value=_saved()):
        r = svc.log_from_command("I ate three eggs", "2026-10-11", FOODS, now=NOW)
    assert r["status"] == "logged"
    kw = create.call_args.kwargs
    assert kw["source"] == "command" and kw["food_id"] == 1
    assert kw["calories_kcal"] is None and kw["nutrition_source"] == "unknown"


def test_unknown_food_asks_unless_confirmed():
    with patch.object(svc.meal_log, "create_log") as create:
        r = svc.log_from_command("I ate 2 pears", "2026-10-11", FOODS, now=NOW)
    assert r["status"] == "clarification"
    create.assert_not_called()
    with patch.object(svc.meal_log, "list_logs", return_value=[]), \
         patch.object(svc.meal_log, "create_log", return_value=9) as create, \
         patch.object(svc.meal_log, "get_log", return_value=_saved(item_name="pears")):
        r = svc.log_from_command("I ate 2 pears", "2026-10-11", FOODS, allow_free_text=True, now=NOW)
    assert r["status"] == "logged" and create.call_args.kwargs["item_type"] == "free_text"


def test_retry_does_not_log_twice():
    with patch.object(svc.meal_log, "list_logs", return_value=[_saved()]), \
         patch.object(svc.meal_log, "create_log") as create:
        r = svc.log_from_command("I ate three eggs", "2026-10-11", FOODS, now=NOW)
    assert r["status"] == "duplicate"
    create.assert_not_called()


def test_same_command_later_is_a_new_meal():
    old = _saved(created_at=NOW - timedelta(hours=3))
    with patch.object(svc.meal_log, "list_logs", return_value=[old]), \
         patch.object(svc.meal_log, "create_log", return_value=10) as create, \
         patch.object(svc.meal_log, "get_log", return_value=_saved(id=10)):
        r = svc.log_from_command("I ate three eggs", "2026-10-11", FOODS, now=NOW)
    assert r["status"] == "logged"
    create.assert_called_once()


def test_undo_last_command_soft_deletes_newest():
    logs = [_saved(id=3), _saved(id=7), _saved(id=8, source="manual")]
    with patch.object(svc.meal_log, "list_logs", return_value=logs), \
         patch.object(svc.meal_log, "soft_delete_log", return_value=True) as delete, \
         patch.object(svc.meal_log, "get_log", return_value=None):
        assert svc.undo_last_command("2026-10-11")["id"] == 7
    delete.assert_called_once_with(7)


if __name__ == "__main__":
    unittest.main()
