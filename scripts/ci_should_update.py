"""GitHub Actions の定期更新が、シーズン中の指定時間帯か判定する。"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
SEASON_START = (3, 25)
SEASON_END = (11, 15)
# 毎日 7:00、平日 18:00〜23:59、土日 13:00〜23:59（JST）
MORNING_HOUR = 7
WEEKDAY_START = 18
WEEKEND_START = 13
WINDOW_END = 23


def in_schedule_window(now: datetime) -> bool:
    local = now.astimezone(JST)
    hour = local.hour
    if hour == MORNING_HOUR:
        return True
    weekday = local.weekday()  # Mon=0 … Sun=6
    start = WEEKDAY_START if weekday < 5 else WEEKEND_START
    return start <= hour <= WINDOW_END


def in_season_dates(day) -> bool:
    start = day.replace(month=SEASON_START[0], day=SEASON_START[1])
    end = day.replace(month=SEASON_END[0], day=SEASON_END[1])
    return start <= day <= end


def should_update(now: datetime | None = None) -> bool:
    current = now.astimezone(JST) if now is not None else datetime.now(JST)
    if not in_schedule_window(current):
        return False
    return in_season_dates(current.date())


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
            f"スキップ: {now.isoformat()} は 3/25〜11/15 の更新時間帯の外です。",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
