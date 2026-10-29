import json
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
    classify_series,
    extra_game_keys,
    format_win_pct,
    last_regular_season_date,
    regular_season_complete,
    shift_ymd,
    victory_history_dates,
    games_behind,
    initial_games_remain,
    load_completed_games,
    matchup_win_pcts,
    pennant_magic,
    remaining_matchups,
    snapshot_through,
    team_stats,
    update_rating,
    update_rating_draw,
    write_today_games,
    write_victory_prob_history,
    build_victory_history,
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

    def test_matchup_win_pcts_from_ratings(self):
        even_a, even_b = matchup_win_pcts(1500, 1500)
        self.assertEqual(even_a, 0.5)
        self.assertEqual(even_b, 0.5)
        fav, dog = matchup_win_pcts(1900, 1500)
        self.assertEqual(fav, round(10 / 11, 4))
        self.assertEqual(dog, round(1 / 11, 4))
        self.assertEqual(matchup_win_pcts(1500, None), (None, None))

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

    def test_extra_games_update_rating_not_standings(self):
        regular = [("2026-04-01", "神", "1", "巨", "0")] * INTRA_LEAGUE_GAMES
        extra = ("2026-10-10", "神", "1", "巨", "0")
        scores, remain, h2h, teams, _teamdict, _updates, _deltas = apply_games(
            [*regular, extra]
        )
        self.assertEqual(scores[TEAMNAMES.index("神")][0], INTRA_LEAGUE_GAMES)
        self.assertEqual(remain[0][3], 0)
        self.assertEqual(h2h[0][3], INTRA_LEAGUE_GAMES)
        regular_teams = apply_games(regular)[3]
        self.assertGreater(teams["神"].rating, regular_teams["神"].rating)
        self.assertEqual(extra_game_keys([*regular, extra]), {("2026-10-10", frozenset(("神", "巨")))})
        self.assertEqual(last_regular_season_date([*regular, extra]), "2026-04-01")


class ClassifySeriesTest(unittest.TestCase):
    def test_labels_climax_and_japan_series(self):
        places = {"神": 1, "デ": 3, "巨": 2, "ソ": 1, "日": 3, "西": 2}
        self.assertEqual(
            classify_series("巨", "デ", places),
            ("クライマックスシリーズ", "ファーストステージ", "central"),
        )
        self.assertEqual(
            classify_series("神", "デ", places),
            ("クライマックスシリーズ", "ファイナルステージ", "central"),
        )
        self.assertEqual(
            classify_series("デ", "ソ", places),
            ("日本シリーズ", "", ""),
        )


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
        self.assertIsNone(rows[0]["a_rating"])
        self.assertIsNone(rows[0]["a_win_pct"])

    def test_attaches_rating_and_win_pct_from_snapshot(self):
        rows = attach_today_deltas(
            [
                {
                    "date": "2026-09-01",
                    "ateam": "巨",
                    "bteam": "デ",
                    "ascore": "4",
                    "bscore": "3",
                    "status": "試合終了",
                }
            ],
            {("2026-09-01", frozenset(("巨", "デ"))): {"巨": 8.0, "デ": -8.0}},
            {"巨": {"rating": 1508.0, "win_pct": "1.000"}, "デ": {"rating": 1492.0, "win_pct": ".000"}},
        )
        self.assertEqual(rows[0]["a_rating"], 1508.0)
        expected_a, expected_b = matchup_win_pcts(1508.0, 1492.0)
        self.assertEqual(rows[0]["a_win_pct"], expected_a)
        self.assertEqual(rows[0]["b_win_pct"], expected_b)


class WriteTodayGamesTest(unittest.TestCase):
    def test_writes_yesterday_results_and_team_stats(self):
        completed = [
            ("2026-09-11", "神", "5", "中", "1"),
            ("2026-09-12", "神", "3", "巨", "2"),
            ("2026-09-13", "ヤ", "1", "中", "0"),
        ]
        scores, _remain, _h2h, teams, _teamdict, _updates, deltas = apply_games(
            completed
        )
        prior_stats, _prior_deltas = snapshot_through(completed, "2026-09-11")
        after_yesterday, _after_deltas = snapshot_through(completed, "2026-09-12")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "today_2026.json"
            output = root / "public"
            output.mkdir()
            source.write_text(
                json.dumps(
                    {
                        "date": "2026-09-13",
                        "games": [
                            {
                                "date": "2026-09-13",
                                "ateam": "ヤ",
                                "bteam": "中",
                                "ascore": "1",
                                "bscore": "0",
                                "status": "試合終了",
                                "venue": "神宮",
                                "note": "",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with (
                patch("compute.today_games_path", return_value=source),
                patch("compute.output_dir", return_value=output),
            ):
                write_today_games(
                    2026,
                    deltas,
                    scores=scores,
                    teams_dict=teams,
                    completed=completed,
                    today=real_date(2026, 9, 13),
                )
            payload = json.loads((output / "today_games.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["date"], "2026-09-13")
        current = team_stats(scores, teams)
        today_game = payload["games"][0]
        today_a, today_b = matchup_win_pcts(
            after_yesterday["ヤ"]["rating"],
            after_yesterday["中"]["rating"],
        )
        self.assertEqual(today_game["a_win_pct"], today_a)
        self.assertEqual(today_game["b_win_pct"], today_b)
        self.assertEqual(today_game["a_rating"], after_yesterday["ヤ"]["rating"])
        self.assertNotEqual(today_game["a_rating"], current["ヤ"]["rating"])
        self.assertAlmostEqual(
            today_game["a_rating"] + today_game["a_delta"],
            current["ヤ"]["rating"],
            places=2,
        )
        yesterday_game = payload["yesterday"]["games"][0]
        self.assertEqual(payload["yesterday"]["date"], "2026-09-12")
        self.assertEqual(yesterday_game["ateam"], "神")
        self.assertEqual(yesterday_game["a_rating"], prior_stats["神"]["rating"])
        y_a, y_b = matchup_win_pcts(prior_stats["神"]["rating"], prior_stats["巨"]["rating"])
        self.assertEqual(yesterday_game["a_win_pct"], y_a)
        self.assertEqual(yesterday_game["b_win_pct"], y_b)
        self.assertNotEqual(yesterday_game["a_rating"], current["神"]["rating"])
        self.assertNotEqual(yesterday_game["a_rating"], after_yesterday["神"]["rating"])
        self.assertAlmostEqual(
            yesterday_game["a_rating"] + yesterday_game["a_delta"],
            current["神"]["rating"],
            places=2,
        )
        self.assertEqual(
            payload["records"]["神"],
            {"wins": scores[0][0], "losses": scores[0][1], "draws": scores[0][2]},
        )
        self.assertEqual(
            yesterday_game["a_delta"],
            round(deltas[("2026-09-12", frozenset(("神", "巨")))]["神"], 2),
        )
        self.assertEqual(current["ヤ"]["win_pct"], "1.000")

    def test_yesterday_uses_jst_game_date(self):
        completed = [("2026-09-16", "神", "3", "巨", "2")]
        scores, _remain, _h2h, teams, _teamdict, _updates, deltas = apply_games(
            completed
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "today_2026.json"
            output = root / "public"
            output.mkdir()
            source.write_text('{"date": "2026-09-17", "games": []}\n', encoding="utf-8")
            with (
                patch("compute.today_games_path", return_value=source),
                patch("compute.output_dir", return_value=output),
                patch("compute.game_date", return_value=real_date(2026, 9, 17)),
            ):
                write_today_games(
                    2026,
                    deltas,
                    scores=scores,
                    teams_dict=teams,
                    completed=completed,
                )
            payload = json.loads((output / "today_games.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["yesterday"]["date"], "2026-09-16")
        self.assertEqual(payload["yesterday"]["games"][0]["ateam"], "神")

    def test_writes_japan_series_cards(self):
        completed = [("2026-04-01", "デ", "1", "ソ", "0")] * INTERLEAGUE_GAMES
        extra = ("2026-10-24", "デ", "2", "ソ", "1")
        completed = [*completed, extra]
        scores, _remain, _h2h, teams, _teamdict, _updates, deltas = apply_games(
            completed
        )
        cards = [
            {
                "date": "2026-10-24",
                "ateam": "デ",
                "bteam": "ソ",
                "ascore": "2",
                "bscore": "1",
                "status": "試合終了",
                "venue": "横浜",
                "note": "",
            },
            {
                "date": "2026-10-25",
                "ateam": "デ",
                "bteam": "ソ",
                "ascore": None,
                "bscore": None,
                "status": "試合前",
                "venue": "横浜",
                "note": "18:00",
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "today_2026.json"
            cards_path = root / "postseason_2026.json"
            output = root / "public"
            output.mkdir()
            source.write_text('{"date": "2026-10-18", "games": []}\n', encoding="utf-8")
            cards_path.write_text(
                json.dumps({"year": 2026, "games": cards}), encoding="utf-8"
            )
            with (
                patch("compute.today_games_path", return_value=source),
                patch("compute.postseason_cards_path", return_value=cards_path),
                patch("compute.output_dir", return_value=output),
            ):
                write_today_games(
                    2026,
                    deltas,
                    scores=scores,
                    teams_dict=teams,
                    completed=completed,
                    today=real_date(2026, 10, 18),
                )
            payload = json.loads((output / "today_games.json").read_text(encoding="utf-8"))
        series = payload["series"]
        self.assertEqual(len(series), 2)
        self.assertEqual(series[0]["series"], "日本シリーズ")
        self.assertEqual(series[0]["game_no"], 1)
        self.assertEqual(series[1]["date"], "2026-10-25")
        self.assertEqual(series[1]["status"], "試合前")
        self.assertEqual(payload["games"], [])
        self.assertIn("places", payload)

    def test_overlays_finished_scores_onto_unplayed_series_cards(self):
        completed = [("2026-04-01", "デ", "1", "ソ", "0")] * INTERLEAGUE_GAMES
        extra = ("2026-10-27", "ソ", "2", "デ", "1")
        completed = [*completed, extra]
        scores, _remain, _h2h, teams, _teamdict, _updates, deltas = apply_games(
            completed
        )
        cards = [
            {
                "date": "2026-10-27",
                "ateam": "ソ",
                "bteam": "デ",
                "ascore": None,
                "bscore": None,
                "status": "試合前",
                "venue": "みずほPayPay",
                "note": "18:00",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "today_2026.json"
            cards_path = root / "postseason_2026.json"
            output = root / "public"
            output.mkdir()
            source.write_text(
                json.dumps(
                    {
                        "date": "2026-10-27",
                        "games": [
                            {
                                "date": "2026-10-27",
                                "ateam": "ソ",
                                "bteam": "デ",
                                "ascore": "2",
                                "bscore": "1",
                                "status": "試合終了",
                                "venue": "みずほPayPay",
                                "note": "",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            cards_path.write_text(
                json.dumps({"year": 2026, "games": cards}), encoding="utf-8"
            )
            with (
                patch("compute.today_games_path", return_value=source),
                patch("compute.postseason_cards_path", return_value=cards_path),
                patch("compute.output_dir", return_value=output),
            ):
                write_today_games(
                    2026,
                    deltas,
                    scores=scores,
                    teams_dict=teams,
                    completed=completed,
                    today=real_date(2026, 10, 27),
                )
            payload = json.loads((output / "today_games.json").read_text(encoding="utf-8"))
        series = payload["series"]
        self.assertEqual(len(series), 1)
        self.assertEqual(series[0]["status"], "試合終了")
        self.assertEqual(series[0]["ascore"], "2")
        self.assertEqual(series[0]["bscore"], "1")
        self.assertEqual(series[0]["venue"], "みずほPayPay")


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


class VictoryHistoryTest(unittest.TestCase):
    def test_history_dates_start_before_opening_and_skip_postseason(self):
        regular = [("2026-04-01", "デ", "1", "ソ", "0")] * INTERLEAGUE_GAMES
        extra = ("2026-10-10", "デ", "2", "ソ", "1")
        games = [*regular, extra]
        self.assertTrue(regular_season_complete(games))
        self.assertEqual(last_regular_season_date(games), "2026-04-01")
        self.assertEqual(
            victory_history_dates(games),
            ["2026-03-31", "2026-04-01", "2026-04-02"],
        )
        self.assertEqual(shift_ymd("2026-04-01", -1), "2026-03-31")

    def test_history_dates_stop_at_last_game_while_season_continues(self):
        games = [
            ("2026-04-01", "神", "3", "中", "1"),
            ("2026-04-02", "神", "2", "巨", "1"),
        ]
        self.assertFalse(regular_season_complete(games))
        self.assertEqual(
            victory_history_dates(games),
            ["2026-03-31", "2026-04-01", "2026-04-02"],
        )

    def test_builds_one_snapshot_per_display_date(self):
        games = [
            ("2026-04-01", "神", "3", "中", "1"),
            ("2026-04-02", "神", "2", "巨", "1"),
        ]
        prev = [99] * 12
        missing = str(Path(tempfile.gettempdir()) / "no-npb-sim")
        with patch.dict(os.environ, {"NPB_SIM_BIN": missing}):
            dates, history, last_ranks = build_victory_history(games, prev, 40)
        self.assertEqual(dates, ["2026-03-31", "2026-04-01", "2026-04-02"])
        self.assertEqual(len(history), 3)
        self.assertEqual(len(history[0]), 12)
        self.assertEqual(len(history[0][0]), 6)
        self.assertAlmostEqual(sum(row[0] for row in history[0][:6]), 100.0, places=1)
        self.assertAlmostEqual(sum(row[0] for row in history[0][6:]), 100.0, places=1)
        self.assertIsNotNone(last_ranks)
        self.assertNotEqual(history[0], history[1])
        self.assertNotEqual(history[1], history[2])

    def test_writes_history_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            with patch("compute.output_dir", return_value=output):
                write_victory_prob_history(
                    ["2026-04-01"],
                    [[[100.0] + [0.0] * 5] + [[0.0] * 6] * 11],
                    40,
                )
            payload = json.loads((output / "victory_prob_history.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["dates"], ["2026-04-01"])
        self.assertEqual(payload["count"], 40)
        self.assertEqual(payload["teams"][0], "神")
        self.assertEqual(payload["probs"][0][0][0], 100.0)

    def test_freezes_ranks_once_postseason_starts(self):
        regular = [("2026-04-01", "デ", "1", "ソ", "0")] * INTERLEAGUE_GAMES
        extra = ("2026-10-10", "デ", "2", "ソ", "1")
        prev = [99] * 12
        missing = str(Path(tempfile.gettempdir()) / "no-npb-sim")
        with patch.dict(os.environ, {"NPB_SIM_BIN": missing}):
            dates, history, last_ranks = build_victory_history(
                [*regular, extra], prev, 20
            )
        self.assertEqual(dates[0], "2026-03-31")
        self.assertEqual(dates[-1], "2026-04-02")
        self.assertNotIn("2026-10-10", dates)
        last = history[-1]
        self.assertTrue(all(abs(sum(row) - 100.0) < 0.01 for row in last))
        self.assertEqual(sum(1 for row in last[:6] if row[0] == 100.0), 1)
        self.assertEqual(sum(1 for row in last[6:] if row[0] == 100.0), 1)
        self.assertEqual(sum(last_ranks[0]), 20)


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
