import tempfile
import unittest
from pathlib import Path

import pathsetup  # noqa: F401
from publish_s3 import (
    cache_control_for,
    content_type_for,
    object_key,
    upload_output_dir,
)


class FakeS3:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def upload_file(self, filename, bucket, key, ExtraArgs=None):
        self.calls.append((filename, bucket, key, ExtraArgs))


class PublishS3Test(unittest.TestCase):
    def test_content_types(self):
        self.assertIn("json", content_type_for(Path("meta.json")))
        self.assertIn("csv", content_type_for(Path("rating.csv")))

    def test_today_games_are_cached_briefly(self):
        self.assertIn("max-age=60", cache_control_for(Path("today_games.json")))
        self.assertIn("max-age=300", cache_control_for(Path("meta.json")))

    def test_object_key_joins_prefix(self):
        self.assertEqual(object_key("data", "meta.json"), "data/meta.json")
        self.assertEqual(object_key("/data/", "meta.json"), "data/meta.json")
        self.assertEqual(object_key("", "meta.json"), "meta.json")

    def test_upload_sends_each_file(self):
        fake = FakeS3()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "meta.json").write_text("{}", encoding="utf-8")
            (root / "today_games.json").write_text("{}", encoding="utf-8")
            (root / "nested").mkdir()
            (root / "nested" / "skip.csv").write_text("x", encoding="utf-8")
            keys = upload_output_dir("bucket", "data", root, fake)
        self.assertEqual(keys, ["data/meta.json", "data/today_games.json"])
        self.assertEqual(len(fake.calls), 2)
        today = next(call for call in fake.calls if call[2].endswith("today_games.json"))
        self.assertEqual(today[3]["CacheControl"], "public, max-age=60")
