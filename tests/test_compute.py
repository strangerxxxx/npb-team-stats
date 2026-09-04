import os
import tempfile
import unittest
from datetime import date as real_date
from pathlib import Path
from unittest.mock import patch

import pathsetup  # noqa: F401
from compute import (
    Player,
    _ensure_rust_sim,
    attach_today_deltas,
    apply_games,
    format_win_pct,
    games_behind,
    initial_games_remain,
    load_completed_games,
    pennant_magic,
    remaining_matchups,
    update_rating,
    update_rating_draw,
)
from config import (
    INITIAL_RATING,
    INTERLEAGUE_GAMES,
    INTRA_LEAGUE_GAMES,
    K_FACTOR,
    file_has_completed_games,
    resolve_year,
)
from teams import TEAMNAMES


class EloTest(unittest.TestCase):
    def test_equal_ratings_are_even(self):
        self.assertAlmostEqual(Player("a").win_proba(Player("b")), 0.5)

    def test_400_point_gap_is_ten_to_one(self):
        favorite = Player("a", 1900)
        underdog = Player("b", 1500)
        self.assertAlmostEqual(favorite.win_proba(underdog), 10 / 11)
        self.assertAlmostEqual(underdog.win_proba(favorite), 1 / 11)

    def test_win_update_is_zero_sum_and_uses_k(self):
        winner, loser = update_rating(Player("神"), Player("巨"))
        self.assertAlmostEqual(winner.rating, INITIAL_RATING + K_FACTOR * 0.5)
        self.assertAlmostEqual(loser.rating, INITIAL_RATING - K_FACTOR * 0.5)
        self.assertAlmostEqual(winner.rating + loser.rating, INITIAL_RATING * 2)

    def test_favorite_gains_less_than_underdog_would(self):
        favorite = Player("ソ", 1900)
        underdog = Player("楽", 1500)
        fav_wins, _dog_loses = update_rating(favorite, underdog)
        dog_wins, _fav_loses = update_rating(underdog, favorite)
        self.assertAlmostEqual(fav_wins.rating - 1900, K_FACTOR / 11)
        self.assertAlmostEqual(dog_wins.rating - 1500, K_FACTOR * 10 / 11)
        self.assertGreater(dog_wins.rating - 1500, fav_wins.rating - 1900)

    def test_draw_between_equals_does_not_move_ratings(self):
        a, b = update_rating_draw(Player("神"), Player("巨"))
        self.assertAlmostEqual(a.rating, INITIAL_RATING)
        self.assertAlmostEqual(b.rating, INITIAL_RATING)

    def test_draw_moves_rating_toward_the_underdog(self):
        favorite, underdog = update_rating_draw(
            Player("ソ", 1900), Player("楽", 1500)
        )
        self.assertLess(favorite.rating, 1900)
        self.assertGreater(underdog.rating, 1500)
        self.assertAlmostEqual(favorite.rating + underdog.rating, 3400)


class FormatAndStandingsHelpersTest(unittest.TestCase):
    def test_format_win_pct(self):
        self.assertEqual(format_win_pct(0, 0), ".000")
        self.assertEqual(format_win_pct(67, 49), ".578")
        self.assertEqual(format_win_pct(1, 0), "1.000")

    def test_games_behind_and_magic(self):
        self.assertEqual(games_behind(67, 49, 63, 54), 4.5)
        self.assertEqual(pennant_magic(67, 63, 24), 21)


class RemainingScheduleTest(unittest.TestCase):
    def test_intra_league_and_interleague_slots(self):
        remain = initial_games_remain()
        self.assertEqual(remain[0][0], 0)
        self.assertEqual(remain[0][1], INTRA_LEAGUE_GAMES)
        self.assertEqual(remain[0][6], INTERLEAGUE_GAMES)
        self.assertEqual(remain[6][0], INTERLEAGUE_GAMES)
        self.assertEqual(remain[8][8], 0)

    def test_remaining_matchups_are_upper_triangle(self):
        remain = initial_games_remain()
        remain[0][1] = 2
        remain[1][0] = 2
        remain[0][6] = 0
        remain[6][0] = 0
        probs = [[0.5] * 12 for _ in range(12)]
        probs[0][1] = 0.6
        matchups = remaining_matchups(remain, probs)
        self.assertIn((0, 1, 2, 0.6), matchups)
        self.assertFalse(any(i == 0 and j == 6 for i, j, _n, _p in matchups))


class LoadCompletedGamesTest(unittest.TestCase):
    def test_skips_invalid_lines_and_sorts_by_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scores.csv"
            path.write_text(
                "2026-03-28,オ,1,西,0\n"
                "not-a-game\n"
                "2026-03-26,神,*,巨,*\n"
                "2026-03-26,神,5,巨,3\n",
                encoding="utf-8",
            )
            self.assertEqual(
                load_completed_games(path),
                [
                    ("2026-03-26", "神", "5", "巨", "3"),
                    ("2026-03-28", "オ", "1", "西", "0"),
                ],
            )


class ApplyGamesTest(unittest.TestCase):
    def test_win_updates_record_h2h_remain_and_rating(self):
        scores, remain, h2h, teams, _teamdict, updates, deltas = apply_games(
            [("2026-03-26", "神", "5", "巨", "3")]
        )
        self.assertEqual(scores[TEAMNAMES.index("神")], [1, 0, 0])
        self.assertEqual(scores[TEAMNAMES.index("巨")], [0, 1, 0])
        self.assertEqual(h2h[TEAMNAMES.index("神")][TEAMNAMES.index("巨")], 1)
        self.assertEqual(h2h[TEAMNAMES.index("巨")][TEAMNAMES.index("神")], 0)
        self.assertEqual(remain[0][3], INTRA_LEAGUE_GAMES - 1)
        self.assertEqual(remain[3][0], INTRA_LEAGUE_GAMES - 1)
        self.assertAlmostEqual(teams["神"].rating, INITIAL_RATING + 8)
        self.assertAlmostEqual(teams["巨"].rating, INITIAL_RATING - 8)
        self.assertAlmostEqual(
            sum(team.rating for team in teams.values()), INITIAL_RATING * 12
        )
        self.assertEqual(
            [name for name, _rating in updates["2026-03-26"]], ["神", "巨"]
        )
        change = deltas[("2026-03-26", frozenset(("神", "巨")))]
        self.assertAlmostEqual(change["神"], 8)
        self.assertAlmostEqual(change["巨"], -8)

    def test_draw_counts_as_draw_and_keeps_equal_ratings(self):
        scores, remain, h2h, teams, _teamdict, _updates, _deltas = apply_games(
            [("2026-03-26", "ソ", "2", "日", "2")]
        )
        self.assertEqual(scores[TEAMNAMES.index("ソ")], [0, 0, 1])
        self.assertEqual(scores[TEAMNAMES.index("日")], [0, 0, 1])
        self.assertEqual(h2h[TEAMNAMES.index("ソ")][TEAMNAMES.index("日")], 0)
        self.assertAlmostEqual(teams["ソ"].rating, INITIAL_RATING)
        self.assertEqual(remain[8][11], INTRA_LEAGUE_GAMES - 1)

    def test_skips_unknown_teams(self):
        scores, _remain, h2h, teams, _teamdict, updates, _deltas = apply_games(
            [("2026-03-26", "神", "1", "??", "0")]
        )
        self.assertEqual(scores[0], [0, 0, 0])
        self.assertEqual(sum(sum(row) for row in h2h), 0)
        self.assertEqual(dict(updates), {})
        self.assertAlmostEqual(teams["神"].rating, INITIAL_RATING)

    def test_interleague_game_decrements_the_three_game_slot(self):
        _scores, remain, _h2h, _teams, _teamdict, _updates, _deltas = apply_games(
            [("2026-06-01", "神", "3", "ソ", "1")]
        )
        self.assertEqual(remain[0][8], INTERLEAGUE_GAMES - 1)
        self.assertEqual(remain[8][0], INTERLEAGUE_GAMES - 1)


class AttachTodayDeltasTest(unittest.TestCase):
    def test_adds_deltas_only_for_finished_games(self):
        _scores, _remain, _h2h, _teams, _teamdict, _updates, deltas = apply_games(
            [("2026-09-01", "巨", "4", "デ", "3")]
        )
        rows = attach_today_deltas(
            [
                {
                    "date": "2026-09-01",
                    "ateam": "巨",
                    "bteam": "デ",
                    "ascore": "4",
                    "bscore": "3",
                    "status": "試合終了",
                },
                {
                    "date": "2026-09-01",
                    "ateam": "ヤ",
                    "bteam": "神",
                    "ascore": "2",
                    "bscore": "1",
                    "status": "試合中",
                },
                {
                    "date": "2026-09-01",
                    "ateam": "中",
                    "bteam": "広",
                    "ascore": None,
                    "bscore": None,
                    "status": "試合前",
                },
            ],
            deltas,
        )
        self.assertEqual(rows[0]["a_delta"], 8.0)
        self.assertEqual(rows[0]["b_delta"], -8.0)
        self.assertIsNone(rows[1]["a_delta"])
        self.assertIsNone(rows[1]["b_delta"])
        self.assertIsNone(rows[2]["a_delta"])


class FileHasCompletedGamesTest(unittest.TestCase):
    def test_true_only_when_a_numeric_score_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scores.csv"
            self.assertFalse(file_has_completed_games(path))
            path.write_text("2026-03-26,神,*,巨,*\n", encoding="utf-8")
            self.assertFalse(file_has_completed_games(path))
            path.write_text("2026-03-26,神,1,巨,0\n", encoding="utf-8")
            self.assertTrue(file_has_completed_games(path))


class ResolveYearTest(unittest.TestCase):
    def test_explicit_year_is_used(self):
        self.assertEqual(resolve_year(2024), 2024)

    @patch("config.has_completed_games")
    @patch("config.date")
    def test_falls_back_to_previous_season_before_opening(self, mock_date, has_games):
        mock_date.today.return_value = real_date(2026, 3, 1)
        has_games.side_effect = lambda year: year == 2025
        self.assertEqual(resolve_year(), 2025)

    @patch("config.has_completed_games")
    @patch("config.date")
    def test_uses_current_year_once_games_exist(self, mock_date, has_games):
        mock_date.today.return_value = real_date(2026, 4, 1)
        has_games.side_effect = lambda year: year == 2026
        self.assertEqual(resolve_year(), 2026)


class SimBinaryTest(unittest.TestCase):
    def test_env_override_returns_existing_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as handle:
            path = handle.name
        try:
            with patch.dict(os.environ, {"NPB_SIM_BIN": path}):
                self.assertEqual(_ensure_rust_sim(), Path(path))
        finally:
            Path(path).unlink(missing_ok=True)

    def test_missing_override_skips_cargo(self):
        with patch.dict(os.environ, {"NPB_SIM_BIN": str(Path(tempfile.gettempdir()) / "no-npb-sim")}):
            self.assertIsNone(_ensure_rust_sim())


if __name__ == "__main__":
    unittest.main()
