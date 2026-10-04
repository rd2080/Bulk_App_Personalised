import unittest
from unittest.mock import patch

from bulking_app.ai.request_builder import build_profile_request


class RequestBuilderTests(unittest.TestCase):
    @patch("bulking_app.ai.request_builder.user_profile.get_user_profile")
    def test_request_contains_current_profile_and_future_extension_points(self, get_profile):
        profile = {"age": 25, "meals_per_day": 5}
        get_profile.return_value = profile
        request = build_profile_request("Create a planning prompt")
        get_profile.assert_called_once_with()
        self.assertIs(request["context"]["user_profile"], profile)
        self.assertIn("food_inventory", request["available_context_sources"])
        self.assertIn("morning_checkin", request["available_context_sources"])

    @patch("bulking_app.ai.request_builder.user_profile.get_user_profile")
    def test_each_call_reads_again(self, get_profile):
        get_profile.side_effect = [{"age": 25}, {"age": 26}]
        first = build_profile_request("Task")
        second = build_profile_request("Task")
        self.assertEqual(first["context"]["user_profile"]["age"], 25)
        self.assertEqual(second["context"]["user_profile"]["age"], 26)
        self.assertEqual(get_profile.call_count, 2)

    def test_empty_task_and_missing_profile_fail_clearly(self):
        with self.assertRaises(ValueError):
            build_profile_request("  ")
        with patch("bulking_app.ai.request_builder.user_profile.get_user_profile", return_value=None):
            with self.assertRaises(RuntimeError):
                build_profile_request("Task")


if __name__ == "__main__":
    unittest.main()
