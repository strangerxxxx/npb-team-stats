import unittest
from pathlib import Path

from bs4 import BeautifulSoup

import pathsetup  # noqa: F401
from scrape import parse_daily_html, parse_schedule_html, team_abbr_from_img, upsert_games

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "schedule.html"
DAILY_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "daily_games.html"


class FakeImg:
    def __init__(self, src):
        self.src = src

    def get(self, key, default=""):
        return self.src if key == "src" else default


class TeamAbbrFromImgTest(unittest.TestCase):
    def test_maps_official_logo_codes(self):
        self.assertEqual(team_abbr_from_img(FakeImg("ini_t_m.png")), "神")
        self.assertEqual(team_abbr_from_img(FakeImg("/img/ini_db_m.png")), "デ")
        self.assertEqual(team_abbr_from_img(FakeImg("ini_h_m.png")), "ソ")
        self.assertEqual(team_abbr_from_img(FakeImg("/img/common/logo/2026/logo_g_m.gif")), "巨")
        self.assertEqual(team_abbr_from_img(FakeImg("logo_db_s.gif")), "デ")

    def test_ignores_unknown_or_missing_codes(self):
        self.assertIsNone(team_abbr_from_img(FakeImg("banner.png")))
        self.assertIsNone(team_abbr_from_img(FakeImg("ini_xx_m.png")))
        self.assertIsNone(team_abbr_from_img(FakeImg("")))


class ParseScheduleHtmlTest(unittest.TestCase):
    def setUp(self):
        self.html = FIXTURE.read_text(encoding="utf-8")

    def test_extracts_completed_games_and_skips_unplayed(self):
        games, _ranks = parse_schedule_html(self.html, 2026, 3)
        self.assertEqual(
            games,
            [
                ("2026-03-26", "神", "5", "巨", "3"),
                ("2026-03-26", "ソ", "2", "日", "2"),
                ("2026-03-28", "オ", "1", "西", "0"),
            ],
        )

    def test_parses_previous_year_rank_from_calendar_order(self):
        _games, ranks = parse_schedule_html(self.html, 2026, 3)
        self.assertEqual(
            ranks,
            {
                "神": 1,
                "デ": 2,
                "巨": 3,
                "中": 4,
                "広": 5,
                "ヤ": 6,
                "ソ": 1,
                "日": 2,
                "オ": 3,
                "楽": 4,
                "西": 5,
                "ロ": 6,
            },
        )

    def test_returns_prev_ranks_when_calendar_is_missing(self):
        soup = BeautifulSoup(self.html, "html.parser")
        soup.find("div", id="calendar").decompose()
        games, ranks = parse_schedule_html(str(soup), 2026, 3)
        self.assertEqual(games, [])
        self.assertEqual(ranks["神"], 1)
        self.assertEqual(ranks["ソ"], 1)


class ParseDailyHtmlTest(unittest.TestCase):
    def test_keeps_only_finished_games(self):
        html = DAILY_FIXTURE.read_text(encoding="utf-8")
        games = parse_daily_html(html, 2026)
        self.assertEqual(games, [("2026-09-01", "巨", "4", "デ", "3")])

    def test_ignores_other_years(self):
        html = DAILY_FIXTURE.read_text(encoding="utf-8")
        self.assertEqual(parse_daily_html(html, 2025), [])


class UpsertGamesTest(unittest.TestCase):
    def test_replaces_same_card_and_appends_new(self):
        existing = [
            ("2026-09-01", "巨", "0", "デ", "0"),
            ("2026-08-30", "神", "5", "広", "1"),
        ]
        extra = [("2026-09-01", "巨", "4", "デ", "3")]
        self.assertEqual(
            upsert_games(existing, extra),
            [
                ("2026-09-01", "巨", "4", "デ", "3"),
                ("2026-08-30", "神", "5", "広", "1"),
            ],
        )
        self.assertEqual(
            upsert_games(existing, [("2026-09-01", "ソ", "2", "日", "1")]),
            existing + [("2026-09-01", "ソ", "2", "日", "1")],
        )


if __name__ == "__main__":
    unittest.main()
