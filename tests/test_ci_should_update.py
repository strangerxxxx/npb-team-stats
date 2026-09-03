import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

import pathsetup  # noqa: F401
from ci_should_update import should_update

JST = ZoneInfo("Asia/Tokyo")


def at(year, month, day, hour, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=JST)


class ShouldUpdateTest(unittest.TestCase):
    def test_opening_day_windows(self):
        self.assertTrue(should_update(at(2026, 3, 25, 7)))
        self.assertTrue(should_update(at(2026, 3, 25, 18)))
        self.assertTrue(should_update(at(2026, 3, 25, 21)))

    def test_weekday_evening_starts_at_18(self):
        # 2026-06-01 は月曜
        self.assertFalse(should_update(at(2026, 6, 1, 17, 59)))
        self.assertTrue(should_update(at(2026, 6, 1, 18)))
        self.assertTrue(should_update(at(2026, 6, 1, 23, 45)))
        self.assertFalse(should_update(at(2026, 6, 1, 4)))
        self.assertFalse(should_update(at(2026, 6, 2, 0)))

    def test_weekend_afternoon_starts_at_13(self):
        # 2026-06-06 は土曜
        self.assertFalse(should_update(at(2026, 6, 6, 12, 59)))
        self.assertTrue(should_update(at(2026, 6, 6, 13)))
        self.assertTrue(should_update(at(2026, 6, 7, 13)))

    def test_morning_slot(self):
        self.assertTrue(should_update(at(2026, 6, 1, 7)))
        self.assertFalse(should_update(at(2026, 6, 1, 8)))

    def test_season_end(self):
        self.assertTrue(should_update(at(2026, 11, 15, 21)))
        self.assertFalse(should_update(at(2026, 11, 16, 7)))
        self.assertFalse(should_update(at(2026, 11, 16, 21)))

    def test_offseason_is_skipped(self):
        self.assertFalse(should_update(at(2026, 3, 24, 18)))
        self.assertFalse(should_update(at(2026, 3, 24, 21)))
        self.assertFalse(should_update(at(2026, 12, 1, 21)))


if __name__ == "__main__":
    unittest.main()
