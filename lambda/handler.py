"""試合結果の取得・計算を行い、公開用ファイルを S3 へ書き出す。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE if (HERE / "scripts").is_dir() else HERE.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ci_should_update import should_update  # noqa: E402
from compute import compute_year  # noqa: E402
from config import output_dir, resolve_year  # noqa: E402
from publish_s3 import upload_output_dir  # noqa: E402
from scrape import run_scrape  # noqa: E402

DEFAULT_SCORES_DIR = "/tmp/npb/scores"
DEFAULT_OUTPUT_DIR = "/tmp/npb/data"
DEFAULT_PREFIX = "data"


def prepare_runtime_env() -> None:
    os.environ.setdefault("NPB_SCORES_DIR", DEFAULT_SCORES_DIR)
    os.environ.setdefault("NPB_OUTPUT_DIR", DEFAULT_OUTPUT_DIR)
    os.environ.setdefault("NPB_SIM_BIN", str(ROOT / "bin" / "npb_sim"))


def is_forced(event: dict | None) -> bool:
    return bool(event and event.get("force"))


def is_schedule_trigger(event: dict | None) -> bool:
    if not event:
        return False
    if event.get("trigger") == "schedule":
        return True
    return event.get("source") in ("aws.events", "aws.scheduler")


def should_run_update(event: dict | None) -> bool:
    if is_forced(event) or not is_schedule_trigger(event):
        return True
    return should_update()


def run_pipeline() -> dict:
    prepare_runtime_env()
    run_scrape()
    year = resolve_year()
    compute_year(year, allow_fallback=True)
    return {"year": year, "output_dir": str(output_dir())}


def publish(output: Path) -> list[str]:
    bucket = os.environ["DATA_BUCKET"]
    prefix = os.environ.get("DATA_PREFIX", DEFAULT_PREFIX)
    import boto3

    return upload_output_dir(bucket, prefix, output, boto3.client("s3"))


def handler(event, context):
    event = event or {}
    if not should_run_update(event):
        return {"ok": True, "skipped": True}

    result = run_pipeline()
    keys = publish(output_dir())
    result.update({"ok": True, "skipped": False, "uploaded": keys})
    return result
