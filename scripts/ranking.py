"""セ・パの公式タイブレークでリーグ内順位を決める。"""

from __future__ import annotations

from collections.abc import Callable, Sequence

KeyFn = Callable[[int, Sequence[int]], float | int]


def win_pct(wins: int | float, losses: int | float) -> float:
    decided = wins + losses
    return wins / decided if decided else 0.0


def overall_wl(h2h: list[list[int]], team: int) -> tuple[int, int]:
    wins = sum(h2h[team])
    losses = sum(h2h[j][team] for j in range(len(h2h)))
    return wins, losses


def h2h_wl(h2h: list[list[int]], team: int, others: Sequence[int]) -> tuple[int, int]:
    wins = sum(h2h[team][j] for j in others if j != team)
    losses = sum(h2h[j][team] for j in others if j != team)
    return wins, losses


def _same(a: float | int, b: float | int) -> bool:
    if isinstance(a, int) and isinstance(b, int):
        return a == b
    return abs(float(a) - float(b)) < 1e-12


def _break_ties(
    indices: Sequence[int],
    key_fn: KeyFn,
    rest: Sequence[KeyFn],
) -> list[int]:
    if len(indices) <= 1:
        return list(indices)
    keys = {i: key_fn(i, indices) for i in indices}
    ordered = sorted(indices, key=lambda i: keys[i], reverse=True)
    if not rest:
        return ordered
    out: list[int] = []
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and _same(keys[ordered[end]], keys[ordered[start]]):
            end += 1
        group = ordered[start:end]
        if len(group) == 1 or not rest:
            out.extend(group)
        else:
            out.extend(_break_ties(group, rest[0], rest[1:]))
        start = end
    return out


def rank_league(
    h2h: list[list[int]],
    prev_ranks: Sequence[int],
    offset: int,
    *,
    central: bool,
) -> list[int]:
    """offset から6チームを公式順で並べ、グローバル索引を返す。"""
    teams = list(range(offset, offset + 6))
    league = teams

    def overall_pct(i: int, _group: Sequence[int]) -> float:
        wins, losses = overall_wl(h2h, i)
        return win_pct(wins, losses)

    def wins_key(i: int, _group: Sequence[int]) -> int:
        return sum(h2h[i])

    def h2h_pct(i: int, group: Sequence[int]) -> float:
        wins, losses = h2h_wl(h2h, i, group)
        return win_pct(wins, losses)

    def intra_pct(i: int, _group: Sequence[int]) -> float:
        wins, losses = h2h_wl(h2h, i, league)
        return win_pct(wins, losses)

    def prev_key(i: int, _group: Sequence[int]) -> int:
        return -int(prev_ranks[i])

    if central:
        steps: list[KeyFn] = [overall_pct, wins_key, h2h_pct, intra_pct, prev_key]
    else:
        steps = [overall_pct, h2h_pct, intra_pct, prev_key]
    return _break_ties(teams, steps[0], steps[1:])
