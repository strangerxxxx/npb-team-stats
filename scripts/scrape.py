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
    game_date,
    has_completed_games,
    postseason_cards_path,
    prev_rank_path,
    resolve_year,
    scores_dir,
    scores_path,
    today_games_path,
)
from teams import TEAM_CODE_TO_ABBR

TEAM_IMG_RE = re.compile(r"(?:ini|logo)_([a-z]+)_[ms]\.(?:gif|png)")
LOGO_CODE_RE = re.compile(r"logo_([a-z]+)_m\.(?:gif|png)")
DAILY_HREF_RE = re.compile(r"/scores/(\d{4})/(\d{2})(\d{2})/")
HEADING_DATE_RE = re.compile(r"(\d{1,2})月(\d{1,2})日")
VENUE_RE = re.compile(r"（([^）]+)）")
TIME_RE = re.compile(r"\d{1,2}:\d{2}")
JP_TIME_RE = re.compile(r"(\d{1,2})時(\d{2})分")
INNING_RE = re.compile(r"\d+回")
FINISHED_MARK = "試合終了"


def start_time_note(state_text: str) -> str:
    colon = TIME_RE.search(state_text)
    if colon:
        return colon.group(0)
    jp = JP_TIME_RE.search(state_text)
    if jp:
        return f"{int(jp.group(1)):d}:{jp.group(2)}"
    return ""


def team_abbr_from_img(img) -> str | None:
    src = img.get("src", "")
    m = TEAM_IMG_RE.search(src)
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


def heading_ymd(text: str, year: int) -> str | None:
    match = HEADING_DATE_RE.search(text or "")
    if not match:
        return None
    return f"{year}-{int(match.group(1)):02d}-{int(match.group(2)):02d}"


def ymd_from_href(href: str, fallback: str | None) -> str | None:
    match = DAILY_HREF_RE.search(href or "")
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return fallback


def parse_game_block(block, ymd: str | None) -> dict[str, str | None] | None:
    imgs = block.select("td.team1 img, td.team2 img")
    if len(imgs) != 2:
        return None
    ateam = team_abbr_from_img(imgs[0])
    bteam = team_abbr_from_img(imgs[1])
    if not ateam or not bteam:
        return None
    date_value = ymd_from_href(block.get("href", ""), ymd)
    if not date_value:
        return None
    scores = [s.get_text(strip=True) for s in block.select("td.score")]
    ascore = scores[0] if len(scores) == 2 and scores[0].isdigit() else None
    bscore = scores[1] if len(scores) == 2 and scores[1].isdigit() else None
    status, venue, note = classify_game_state(block, ascore is not None)
    return {
        "date": date_value,
        "ateam": ateam,
        "bteam": bteam,
        "ascore": ascore,
        "bscore": bscore,
        "status": status,
        "venue": venue,
        "note": note,
    }


def parse_calendar_cards(
    calendar, year: int, month: int
) -> list[dict[str, str | None]]:
    cards: list[dict[str, str | None]] = []
    for td in calendar.find_all("td"):
        date_el = td.find("div", class_="date")
        if date_el is None:
            continue
        date_text = date_el.get_text(strip=True)
        if not date_text.isdigit():
            continue
        ymd = f"{year}-{month:02}-{int(date_text):02}"
        for link in td.select("a.link_block"):
            game = parse_game_block(link, ymd)
            if game and str(game["date"]).startswith(f"{year}-"):
                cards.append(game)
    return cards


def parse_calendar_games(
    calendar, year: int, month: int
) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for game in parse_calendar_cards(calendar, year, month):
        ascore, bscore = game["ascore"], game["bscore"]
        if not ascore or not bscore:
            continue
        if game["status"] == "試合中止":
            continue
        rows.append(
            (game["date"], game["ateam"], ascore, game["bteam"], bscore)
        )
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


def parse_month(
    year: int, month: int
) -> tuple[list[tuple[str, str, str, str, str]], dict[str, int], list[dict[str, str | None]]]:
    url = f"https://npb.jp/games/{year}/schedule_{month:02}.html"
    res = requests.get(url, timeout=30)
    res.raise_for_status()
    games, prev_ranks = parse_schedule_html(res.content, year, month)
    soup = BeautifulSoup(res.content, "html.parser")
    calendar = soup.find("div", id="calendar")
    cards = parse_calendar_cards(calendar, year, month) if calendar else []
    return games, prev_ranks, cards


def parse_schedule_section(
    soup: BeautifulSoup, year: int
) -> list[dict[str, str | None]]:
    root = soup.find("div", id="schedule_section")
    if root is None:
        return []
    games: list[dict[str, str | None]] = []
    for block_el in root.select("div.block"):
        heading = block_el.find("h6")
        ymd = heading_ymd(heading.get_text(" ", strip=True) if heading else "", year)
        for link in block_el.select("a.link_block"):
            game = parse_game_block(link, ymd)
            if game and str(game["date"]).startswith(f"{year}-"):
                games.append(game)
    return games


def parse_daily_html(
    html: str | bytes, year: int
) -> list[dict[str, str | None]]:
    """https://npb.jp/games/{year}/ の試合速報から当日カードを取り出す。"""
    soup = BeautifulSoup(html, "html.parser")
    root = soup.find("div", id="game_score")
    heading = None
    games: list[dict[str, str | None]] = []
    if root is not None:
        h5 = root.find("h5")
        heading = heading_ymd(h5.get_text(" ", strip=True) if h5 else "", year)
        for block in root.select("a.link_block"):
            game = parse_game_block(block, heading)
            if game and str(game["date"]).startswith(f"{year}-"):
                games.append(game)
    if games:
        return games
    week = parse_schedule_section(soup, year)
    if heading:
        return [game for game in week if game["date"] == heading]
    return []


def classify_game_state(block, has_scores: bool) -> tuple[str, str, str]:
    state_text = " ".join(s.get_text(" ", strip=True) for s in block.select("td.state"))
    compact = re.sub(r"\s+", "", state_text)
    venue_match = VENUE_RE.search(state_text)
    venue = venue_match.group(1).replace("　", "").strip() if venue_match else ""
    if not venue:
        leftover = VENUE_RE.sub("", state_text)
        leftover = re.sub(
            r"試合終了|試合中止|試合中|試合前",
            "",
            leftover,
        )
        leftover = TIME_RE.sub("", leftover)
        leftover = JP_TIME_RE.sub("", leftover)
        leftover = INNING_RE.sub("", leftover)
        venue = leftover.replace("　", "").strip()

    if FINISHED_MARK in compact:
        return "試合終了", venue, ""
    if "試合中止" in compact or (compact.endswith("中止") and "回" not in compact):
        return "試合中止", venue, ""
    time_note = start_time_note(state_text)
    inning_match = INNING_RE.search(compact)
    if inning_match or "試合中" in compact:
        note = ""
        if inning_match:
            start = compact.find(inning_match.group(0))
            note = compact[start:]
        return "試合中", venue, note
    if time_note:
        return "試合前", venue, time_note
    if has_scores:
        return "試合終了", venue, ""
    return "試合前", venue, ""


def finished_game_rows(
    daily: list[dict[str, str | None]],
) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for game in daily:
        if game["status"] != "試合終了":
            continue
        ascore, bscore = game["ascore"], game["bscore"]
        if not ascore or not bscore:
            continue
        rows.append(
            (game["date"], game["ateam"], ascore, game["bteam"], bscore)
        )
    return rows


def fetch_daily_games(year: int) -> list[dict[str, str | None]]:
    url = f"https://npb.jp/games/{year}/"
    res = requests.get(url, timeout=30)
    res.raise_for_status()
    return parse_daily_html(res.content, year)


def write_today_games(year: int, daily: list[dict[str, str | None]]) -> None:
    path = today_games_path(year)
    path.parent.mkdir(parents=True, exist_ok=True)
    date_value = daily[0]["date"] if daily else game_date().strftime("%Y-%m-%d")
    path.write_text(
        json.dumps({"date": date_value, "games": daily}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )


def write_postseason_cards(year: int, cards: list[dict[str, str | None]]) -> None:
    path = postseason_cards_path(year)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"year": year, "games": cards}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )


def merge_postseason_cards(
    cards: list[dict[str, str | None]],
    daily: list[dict[str, str | None]],
) -> list[dict[str, str | None]]:
    """当日ページの確定結果を、カレンダー由来のポストシーズンカードへ反映する。"""
    index = {
        (card.get("date"), frozenset((card.get("ateam"), card.get("bteam")))): i
        for i, card in enumerate(cards)
        if card.get("ateam") and card.get("bteam")
    }
    out = [dict(card) for card in cards]
    for game in daily:
        ateam, bteam = game.get("ateam"), game.get("bteam")
        date_value = game.get("date")
        if not ateam or not bteam or not date_value:
            continue
        key = (date_value, frozenset((ateam, bteam)))
        if key not in index:
            continue
        merged = dict(out[index[key]])
        for field in ("ascore", "bscore", "status", "venue", "note"):
            if game.get(field) not in (None, ""):
                merged[field] = game[field]
        out[index[key]] = merged
    return out


def upsert_games(
    games: list[tuple[str, str, str, str, str]],
    extra: list[tuple[str, str, str, str, str]],
) -> list[tuple[str, str, str, str, str]]:
    """同じ日の同一カードは extra で上書きする。"""
    index = {
        (ymd, frozenset((ateam, bteam))): i
        for i, (ymd, ateam, _ascore, bteam, _bscore) in enumerate(games)
    }
    out = list(games)
    for game in extra:
        ymd, ateam, _ascore, bteam, _bscore = game
        key = (ymd, frozenset((ateam, bteam)))
        if key in index:
            out[index[key]] = game
        else:
            index[key] = len(out)
            out.append(game)
    return out


def scrape_year(year: int) -> tuple[list[str], dict[str, int]]:
    scores_dir().mkdir(parents=True, exist_ok=True)
    games: list[tuple[str, str, str, str, str]] = []
    prev_ranks: dict[str, int] = {}
    postseason_cards: list[dict[str, str | None]] = []
    # 開幕が3月の年もあるため 3〜11 月を対象にする
    months = range(3, 12)
    last_month = 11
    for month in months:
        try:
            month_games, ranks, cards = parse_month(year, month)
            games.extend(month_games)
            if month >= 10:
                postseason_cards.extend(cards)
            if ranks and not prev_ranks:
                prev_ranks = ranks
        except requests.RequestException:
            pass
        if month < last_month:
            time.sleep(1)

    if year == date.today().year:
        try:
            daily = fetch_daily_games(year)
            games = upsert_games(games, finished_game_rows(daily))
            write_today_games(year, daily)
            postseason_cards = merge_postseason_cards(postseason_cards, daily)
        except requests.RequestException:
            pass

    if postseason_cards:
        write_postseason_cards(year, postseason_cards)

    lines = [
        f"{ymd},{ateam},{ascore},{bteam},{bscore}\n"
        for ymd, ateam, ascore, bteam, bscore in games
    ]
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


def run_scrape(year: int | None = None) -> int:
    """試合結果を取得して scores CSV に書き出す。対象年度を返す。"""
    target = year if year is not None else date.today().year
    lines, prev_ranks = scrape_year(target)
    out_path = scores_path(target)
    if not lines:
        if year is None and out_path.exists() and not has_completed_games(target):
            out_path.unlink()
        display_year = resolve_year()
        if display_year != target:
            print(
                f"{target}年は開幕前か試合がないため、表示・計算は {display_year} 年の結果を使います。"
            )
        else:
            print(f"{target}年の試合結果は見つかりませんでした。")
        write_prev_ranks(target, prev_ranks)
        return target

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.writelines(lines)
    write_prev_ranks(target, prev_ranks)
    print(f"{target}年の試合を {len(lines)} 件書き出しました: {out_path}")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="NPBの試合結果を取得する")
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="対象年度（省略時は実行年。試合がなければファイルは作らない）",
    )
    args = parser.parse_args()
    run_scrape(args.year)


if __name__ == "__main__":
    main()
