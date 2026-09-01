"""NPB公式サイトから試合結果を取得し、data/scores/scores_{year}.csv に書き出す。"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import date

import requests
from bs4 import BeautifulSoup
from config import (
    SCORES_DIR,
    has_completed_games,
    prev_rank_path,
    resolve_year,
    scores_path,
)
from teams import TEAM_CODE_TO_ABBR

TEAM_CODE_RE = re.compile(r"ini_([a-z]+)_m\.png")
LOGO_CODE_RE = re.compile(r"logo_([a-z]+)_m\.(?:gif|png)")


def team_abbr_from_img(img) -> str | None:
    src = img.get("src", "")
    m = TEAM_CODE_RE.search(src)
    if not m:
        return None
    return TEAM_CODE_TO_ABBR.get(m.group(1))


def parse_prev_ranks(soup: BeautifulSoup) -> dict[str, int]:
    """球団別カレンダーは左が前年度上位。リーグごとに 1〜6。"""
    block = soup.select_one(".new_team_list_12team")
    if block is None:
        return {}
    ranks: dict[str, int] = {}
    for ul in block.select("ul.league"):
        place = 1
        for img in ul.select("li img"):
            match = LOGO_CODE_RE.search(img.get("src", ""))
            if not match:
                continue
            abbr = TEAM_CODE_TO_ABBR.get(match.group(1))
            if not abbr:
                continue
            ranks[abbr] = place
            place += 1
    return ranks


def parse_calendar_games(
    calendar, year: int, month: int
) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for td in calendar.find_all("td"):
        date_el = td.find("div", class_="date")
        if date_el is None:
            continue
        date_text = date_el.get_text(strip=True)
        if not date_text.isdigit():
            continue

        ymd = f"{year}-{month:02}-{int(date_text):02}"
        for link in td.select("a.link_block"):
            scores = [s.get_text(strip=True) for s in link.select("td.score")]
            if len(scores) != 2:
                continue
            # 未開催・中止などは "*" などになるためスキップ
            if not scores[0].isdigit() or not scores[1].isdigit():
                continue

            imgs = link.select("td.team1 img, td.team2 img")
            if len(imgs) != 2:
                continue
            ateam = team_abbr_from_img(imgs[0])
            bteam = team_abbr_from_img(imgs[1])
            if not ateam or not bteam:
                continue

            rows.append((ymd, ateam, scores[0], bteam, scores[1]))
    return rows


def parse_schedule_html(
    html: str | bytes, year: int, month: int
) -> tuple[list[tuple[str, str, str, str, str]], dict[str, int]]:
    soup = BeautifulSoup(html, "html.parser")
    calendar = soup.find("div", id="calendar")
    prev_ranks = parse_prev_ranks(soup)
    if calendar is None:
        return [], prev_ranks
    return parse_calendar_games(calendar, year, month), prev_ranks


def parse_month(year: int, month: int) -> tuple[list[tuple[str, str, str, str, str]], dict[str, int]]:
    url = f"https://npb.jp/games/{year}/schedule_{month:02}.html"
    res = requests.get(url, timeout=30)
    res.raise_for_status()
    return parse_schedule_html(res.content, year, month)


def scrape_year(year: int) -> tuple[list[str], dict[str, int]]:
    SCORES_DIR.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    prev_ranks: dict[str, int] = {}
    # 開幕が3月の年もあるため 3〜11 月を対象にする
    months = range(3, 12)
    last_month = 11
    for month in months:
        try:
            games, ranks = parse_month(year, month)
            for ymd, ateam, ascore, bteam, bscore in games:
                lines.append(f"{ymd},{ateam},{ascore},{bteam},{bscore}\n")
            if ranks and not prev_ranks:
                prev_ranks = ranks
        except requests.RequestException:
            pass
        if month < last_month:
            time.sleep(1)
    return lines, prev_ranks


def write_prev_ranks(year: int, prev_ranks: dict[str, int]) -> None:
    if not prev_ranks:
        return
    path = prev_rank_path(year)
    path.write_text(
        json.dumps(prev_ranks, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"前年度順位を書き出しました: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="NPBの試合結果を取得する")
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="対象年度（省略時は実行年。試合がなければファイルは作らない）",
    )
    args = parser.parse_args()
    year = args.year if args.year is not None else date.today().year
    lines, prev_ranks = scrape_year(year)
    out_path = scores_path(year)
    if not lines:
        if args.year is None and out_path.exists() and not has_completed_games(year):
            out_path.unlink()
        display_year = resolve_year()
        if display_year != year:
            print(
                f"{year}年は開幕前か試合がないため、表示・計算は {display_year} 年の結果を使います。"
            )
        else:
            print(f"{year}年の試合結果は見つかりませんでした。")
        write_prev_ranks(year, prev_ranks)
        return

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.writelines(lines)
    write_prev_ranks(year, prev_ranks)
    print(f"{year}年の試合を {len(lines)} 件書き出しました: {out_path}")


if __name__ == "__main__":
    main()
