import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
LAMBDA_DIR = ROOT / "lambda"
if str(LAMBDA_DIR) not in sys.path:
    sys.path.insert(0, str(LAMBDA_DIR))

from handler import should_run_update  # noqa: E402


class HandlerGateTest(unittest.TestCase):
    def test_manual_invoke_always_runs(self):
        self.assertTrue(should_run_update({}))
        self.assertTrue(should_run_update(None))

    def test_force_runs_outside_the_window(self):
        with patch("handler.should_update", return_value=False):
            self.assertTrue(should_run_update({"force": True, "trigger": "schedule"}))

    def test_schedule_respects_season_window(self):
        with patch("handler.should_update", return_value=False):
            self.assertFalse(should_run_update({"trigger": "schedule"}))
        with patch("handler.should_update", return_value=True):
            self.assertTrue(should_run_update({"trigger": "schedule"}))
