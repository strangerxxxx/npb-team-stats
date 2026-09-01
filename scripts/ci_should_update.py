"""GitHub Actions の定期更新が、シーズン中の指定時間帯か判定する。"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
SEASON_START = (3, 25)
SEASON_END = (11, 15)
# 21:00〜27:00 JST（翌 3:00 を含む）
HOURLY_START = 21
OVERNIGHT_END = 3


def season_day(now: datetime) -> datetime.date:
    """0:00〜3:00 は前日夜の延長とみなす。"""
    local = now.astimezone(JST)
    if local.hour <= OVERNIGHT_END:
        return (local - timedelta(days=1)).date()
    return local.date()


def in_hourly_window(now: datetime) -> bool:
    hour = now.astimezone(JST).hour
    return hour >= HOURLY_START or hour <= OVERNIGHT_END


def in_season_dates(day) -> bool:
    start = day.replace(month=SEASON_START[0], day=SEASON_START[1])
    end = day.replace(month=SEASON_END[0], day=SEASON_END[1])
    return start <= day <= end


def should_update(now: datetime | None = None) -> bool:
    current = now.astimezone(JST) if now is not None else datetime.now(JST)
    if not in_hourly_window(current):
        return False
    return in_season_dates(season_day(current))


def main() -> None:
    require_window = os.environ.get("REQUIRE_SEASON_WINDOW", "").lower() == "true"
    now = datetime.now(JST)
    ok = True if not require_window else should_update(now)
    value = "true" if ok else "false"
    output = os.environ.get("GITHUB_OUTPUT")
    line = f"should_update={value}\n"
    if output:
        with open(output, "a", encoding="utf-8") as fh:
            fh.write(line)
    else:
        sys.stdout.write(line)
    if require_window and not ok:
        print(
            f"スキップ: {now.isoformat()} は 3/25〜11/15 の 21:00〜27:00 JST の外です。",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
