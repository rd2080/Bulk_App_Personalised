import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from bulking_app.repositories.user_profile import (
    PROFILE_FIELDS, get_user_profile, upsert_user_profile, validate_profile,
)


def valid_profile():
    return {
        "age": 25, "height_cm": 175.5, "target_weight_kg": 70,
        "diet_type": "vegetarian with eggs", "diet_philosophy": "easy adherence",
        "calorie_strategy": "gradual surplus", "cuisine_preference": "Indian",
        "regional_context": "Mumbai, Maharashtra", "cooking_complexity": "minimal",
        "meals_per_day": 5,
    }


class UserProfileTests(unittest.TestCase):
    def test_validation_normalizes_values_and_has_exact_fields(self):
        result = validate_profile(valid_profile())
        self.assertEqual(tuple(result), PROFILE_FIELDS)
        self.assertEqual(result["height_cm"], Decimal("175.5"))
        self.assertEqual(result["diet_type"], "vegetarian with eggs")

    def test_validation_rejects_missing_extra_and_out_of_range_values(self):
        profile = valid_profile()
        with self.assertRaises(ValueError):
            validate_profile({key: val for key, val in profile.items() if key != "age"})
        with self.assertRaises(ValueError):
            validate_profile({**profile, "name": "not allowed"})
        with self.assertRaises(ValueError):
            validate_profile({**profile, "meals_per_day": 0})
        with self.assertRaises(ValueError):
            validate_profile({**profile, "regional_context": " "})

    @patch("bulking_app.repositories.user_profile.connection")
    def test_get_returns_profile_or_none(self, connection_mock):
        conn = MagicMock()
        connection_mock.return_value.__enter__.return_value = conn
        conn.execute.return_value.fetchone.return_value = tuple(valid_profile().values())
        self.assertEqual(get_user_profile()["age"], 25)
        conn.execute.return_value.fetchone.return_value = None
        self.assertIsNone(get_user_profile())

    @patch("bulking_app.repositories.user_profile.connection")
    def test_upsert_validates_then_executes_singleton_upsert(self, connection_mock):
        conn = MagicMock()
        connection_mock.return_value.__enter__.return_value = conn
        result = upsert_user_profile(valid_profile())
        self.assertEqual(result["age"], 25)
        self.assertEqual(conn.execute.call_count, 2)
        query, params = conn.execute.call_args.args
        self.assertIn("ON CONFLICT ((true)) DO UPDATE", query)
        self.assertEqual(len(params), 10)

    @patch("bulking_app.repositories.user_profile.connection")
    def test_invalid_profile_never_touches_database(self, connection_mock):
        with self.assertRaises(ValueError):
            upsert_user_profile({**valid_profile(), "age": 200})
        connection_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
