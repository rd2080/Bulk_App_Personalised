import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from bulking_app.repositories.morning_checkin import (
    get_morning_checkin, recent_morning_checkins, save_morning_checkin,
)


class MorningCheckinTests(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.conn.__enter__.return_value = self.conn

    @patch("bulking_app.repositories.morning_checkin.connection")
    def test_save_upserts_checkin_and_weight(self, connection_mock):
        connection_mock.return_value = self.conn
        self.conn.execute.side_effect = [MagicMock(fetchone=MagicMock(return_value=(3,))),
                                         MagicMock(fetchone=MagicMock(return_value=(9,)))]
        result = save_morning_checkin(checkin_date="2026-10-04", weight_kg=72.3,
                                      sleep_hours=7.5, soreness_level=4, daily_notes="  Rest day  ")
        self.assertEqual(result, 9)
        self.assertEqual(self.conn.execute.call_count, 2)
        self.assertEqual(self.conn.execute.call_args_list[0].args[1][0], date(2026, 10, 4))
        self.assertEqual(self.conn.execute.call_args_list[0].args[1][-1], "Rest day")

    def test_invalid_values_are_rejected_before_database_access(self):
        with patch("bulking_app.repositories.morning_checkin.connection") as connection_mock:
            for fields in ({"weight_kg": 10}, {"sleep_hours": 25}, {"soreness_level": 0}):
                args = dict(checkin_date="2026-10-04", weight_kg=72,
                            sleep_hours=7, soreness_level=3, daily_notes="")
                args.update(fields)
                with self.assertRaises(ValueError):
                    save_morning_checkin(**args)
            connection_mock.assert_not_called()

    @patch("bulking_app.repositories.morning_checkin.connection")
    def test_get_and_list_return_saved_fields(self, connection_mock):
        connection_mock.return_value = self.conn
        self.conn.execute.return_value.fetchone.return_value = (
            date(2026, 10, 4), 72.3, 7.5, 4, None
        )
        self.assertEqual(get_morning_checkin("2026-10-04")["weight_kg"], 72.3)
        self.conn.execute.return_value.fetchall.return_value = [
            (date(2026, 10, 4), 72.3, 7.5, 4, "")
        ]
        self.assertEqual(len(recent_morning_checkins()), 1)


if __name__ == "__main__":
    unittest.main()
