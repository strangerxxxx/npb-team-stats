import os
from datetime import date
from pathlib import Path

K_FACTOR = 16
SIMULATION_COUNT = 10**5
INITIAL_RATING = 1500.0
# 同一リーグ対戦: 25試合、交流戦: 各3試合（年間143試合）
INTRA_LEAGUE_GAMES = 25
INTERLEAGUE_GAMES = 3

ROOT = Path(__file__).resolve().parent.parent


def scores_dir() -> Path:
    raw = os.environ.get("NPB_SCORES_DIR")
    return Path(raw) if raw else ROOT / "data" / "scores"


def output_dir() -> Path:
    raw = os.environ.get("NPB_OUTPUT_DIR")
    return Path(raw) if raw else ROOT / "public" / "data"


def scores_path(year: int) -> Path:
    return scores_dir() / f"scores_{year}.csv"


def today_games_path(year: int) -> Path:
    return scores_dir() / f"today_{year}.json"


def prev_rank_path(year: int) -> Path:
    return scores_dir() / f"prev_rank_{year}.json"


def file_has_completed_games(path: Path) -> bool:
    if not path.exists():
        return False
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip().split(",")
            if len(parts) >= 5 and parts[2].isdigit() and parts[4].isdigit():
                return True
    return False


def has_completed_games(year: int) -> bool:
    return file_has_completed_games(scores_path(year))


def resolve_year(requested: int | None = None) -> int:
    """表示・計算する年度。開幕前で今季の試合がなければ前年度。"""
    if requested is not None:
        return requested
    year = date.today().year
    if has_completed_games(year):
        return year
    if has_completed_games(year - 1):
        return year - 1
    return year
