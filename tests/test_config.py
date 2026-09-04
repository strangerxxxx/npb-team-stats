import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pathsetup  # noqa: F401
from config import output_dir, scores_dir


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
