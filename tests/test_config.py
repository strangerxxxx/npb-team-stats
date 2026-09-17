import os
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pathsetup  # noqa: F401
from config import game_date, output_dir, scores_dir

JST = ZoneInfo("Asia/Tokyo")
UTC = ZoneInfo("UTC")


class ConfigPathTest(unittest.TestCase):
    def test_default_dirs_are_under_the_repo(self):
        with patch.dict(os.environ):
            os.environ.pop("NPB_SCORES_DIR", None)
            os.environ.pop("NPB_OUTPUT_DIR", None)
            self.assertEqual(scores_dir().name, "scores")
            self.assertEqual(output_dir().name, "data")
            self.assertEqual(scores_dir().parent.name, "data")
            self.assertEqual(output_dir().parent.name, "public")

    def test_env_overrides_are_read_on_each_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            scores = Path(tmp) / "scores"
            public = Path(tmp) / "out"
            with patch.dict(
                os.environ,
                {
                    "NPB_SCORES_DIR": str(scores),
                    "NPB_OUTPUT_DIR": str(public),
                },
            ):
                self.assertEqual(scores_dir(), scores)
                self.assertEqual(output_dir(), public)


class GameDateTest(unittest.TestCase):
    def test_after_5am_jst_is_that_calendar_day(self):
        self.assertEqual(
            game_date(datetime(2026, 9, 17, 5, 0, tzinfo=JST)),
            date(2026, 9, 17),
        )
        self.assertEqual(
            game_date(datetime(2026, 9, 17, 8, 59, tzinfo=JST)),
            date(2026, 9, 17),
        )

    def test_before_5am_jst_is_previous_calendar_day(self):
        self.assertEqual(
            game_date(datetime(2026, 9, 17, 4, 59, tzinfo=JST)),
            date(2026, 9, 16),
        )
        self.assertEqual(
            game_date(datetime(2026, 9, 17, 0, 0, tzinfo=JST)),
            date(2026, 9, 16),
        )

    def test_utc_before_midnight_maps_to_jst_morning(self):
        # 08:59 JST = 23:59 UTC previous day（Lambda の date.today() がずれる時間帯）
        self.assertEqual(
            game_date(datetime(2026, 9, 16, 23, 59, tzinfo=UTC)),
            date(2026, 9, 17),
        )
