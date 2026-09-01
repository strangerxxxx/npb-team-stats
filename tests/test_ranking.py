import unittest

import pathsetup  # noqa: F401
from ranking import rank_league


def empty_h2h(n=12):
    return [[0] * n for _ in range(n)]


def prev_ranks():
    return list(range(1, 13))


class RankLeagueTest(unittest.TestCase):
    def test_orders_by_win_pct(self):
        h2h = empty_h2h()
        h2h[0][5] = 10
        h2h[1][5] = 5
        h2h[5][1] = 5
        order = rank_league(h2h, prev_ranks(), 0, central=True)
        self.assertEqual(order[0], 0)
        self.assertEqual(order[1], 1)

    def test_central_breaks_equal_pct_by_wins_before_h2h(self):
        h2h = empty_h2h()
        # Team 0: 20-20, team 1: 10-10, but team 1 won the season series 8-2.
        h2h[0][1] = 2
        h2h[1][0] = 8
        h2h[0][5] = 18
        h2h[5][0] = 12
        h2h[1][5] = 2
        h2h[5][1] = 8
        h2h[4][5] = 20
        order = rank_league(h2h, prev_ranks(), 0, central=True)
        self.assertLess(order.index(0), order.index(1))

    def test_pacific_breaks_equal_pct_by_h2h_not_wins(self):
        h2h = empty_h2h()
        h2h[0][1] = 2
        h2h[1][0] = 8
        h2h[0][5] = 18
        h2h[5][0] = 12
        h2h[1][5] = 2
        h2h[5][1] = 8
        h2h[4][5] = 20
        order = rank_league(h2h, prev_ranks(), 0, central=False)
        self.assertLess(order.index(1), order.index(0))

    def test_previous_year_rank_breaks_identical_records(self):
        h2h = empty_h2h()
        h2h[0][5] = 5
        h2h[5][0] = 5
        h2h[1][5] = 5
        h2h[5][1] = 5
        h2h[4][5] = 20
        prev = prev_ranks()
        prev[0] = 5
        prev[1] = 1
        order = rank_league(h2h, prev, 0, central=True)
        self.assertLess(order.index(1), order.index(0))


if __name__ == "__main__":
    unittest.main()
