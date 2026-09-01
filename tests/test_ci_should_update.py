import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

import pathsetup  # noqa: F401
from ci_should_update import should_update

JST = ZoneInfo("Asia/Tokyo")


def at(year, month, day, hour, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=JST)


class ShouldUpdateTest(unittest.TestCase):
    def test_opening_day_evening_runs(self):
        self.assertTrue(should_update(at(2026, 3, 25, 21)))
        self.assertTrue(should_update(at(2026, 3, 26, 3)))

    def test_hours_outside_21_to_27_are_skipped(self):
        self.assertFalse(should_update(at(2026, 6, 1, 20, 59)))
        self.assertFalse(should_update(at(2026, 6, 1, 4)))
        self.assertTrue(should_update(at(2026, 6, 1, 21)))
        self.assertTrue(should_update(at(2026, 6, 2, 0)))
        self.assertTrue(should_update(at(2026, 6, 2, 3)))

    def test_night_slot_before_opening_is_skipped(self):
        self.assertFalse(should_update(at(2026, 3, 25, 3)))

    def test_season_end_includes_following_3am(self):
        self.assertTrue(should_update(at(2026, 11, 15, 21)))
        self.assertTrue(should_update(at(2026, 11, 16, 3)))
        self.assertFalse(should_update(at(2026, 11, 16, 21)))

    def test_offseason_is_skipped(self):
        self.assertFalse(should_update(at(2026, 3, 24, 21)))
        self.assertFalse(should_update(at(2026, 12, 1, 21)))


if __name__ == "__main__":
    unittest.main()
