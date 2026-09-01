"""試合結果からレーティング・順位予想を計算し、public/data/ にCSVを書き出す。"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import random
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from config import (
    INITIAL_RATING,
    INTERLEAGUE_GAMES,
    INTRA_LEAGUE_GAMES,
    K_FACTOR,
    OUTPUT_DIR,
    SIMULATION_COUNT,
    has_completed_games,
    prev_rank_path,
    resolve_year,
    scores_path,
)
from ranking import rank_league
from teams import CENTRAL, PACIFIC, TEAMNAMES

RNG = random.Random(10)


class Player:
    def __init__(self, name: str, rating: float = INITIAL_RATING) -> None:
        self.name = name
        self.rating = rating

    def win_proba(self, other: "Player") -> float:
        return 1.0 / (10.0 ** ((other.rating - self.rating) / 400.0) + 1.0)

    def __str__(self) -> str:
        return f"{self.name}: {self.rating:.2f}"


def update_rating(winner: Player, loser: Player) -> tuple[Player, Player]:
    """Elo: Δ = K * (S - E). 勝者 S=1 なので Δ = K * E_loser。"""
    expected_loser_win = loser.win_proba(winner)
    new_winner = Player(winner.name, winner.rating + K_FACTOR * expected_loser_win)
    new_loser = Player(loser.name, loser.rating - K_FACTOR * expected_loser_win)
    return new_winner, new_loser


def update_rating_draw(player_a: Player, player_b: Player) -> tuple[Player, Player]:
    """引き分け S=0.5。Δ_a = K * (0.5 - E_a) = K * (E_b - 0.5)。"""
    expected_b_win = player_b.win_proba(player_a)
    new_a = Player(player_a.name, player_a.rating + K_FACTOR * (expected_b_win - 0.5))
    new_b = Player(player_b.name, player_b.rating - K_FACTOR * (expected_b_win - 0.5))
    return new_a, new_b


def format_win_pct(wins: float, losses: float) -> str:
    """NPB風の勝率表記（例: .562）。1.000 はそのまま返す。"""
    decided = wins + losses
    if decided == 0:
        return ".000"
    pct = wins / decided
    if pct >= 1.0:
        return "1.000"
    return f"{pct:.3f}"[1:]


def win_pct(wins: int | float, losses: int | float) -> float:
    decided = wins + losses
    return wins / decided if decided else 0.0


def load_prev_ranks(year: int) -> list[int]:
    path = prev_rank_path(year)
    data: dict[str, int] = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    return [int(data.get(name, 99)) for name in TEAMNAMES]


def initial_games_remain() -> list[list[int]]:
    games = [[INTRA_LEAGUE_GAMES] * 12 for _ in range(12)]
    for i in range(6):
        games[i][i] = 0
        games[i + 6][i + 6] = 0
        for j in range(6, 12):
            games[i][j] = INTERLEAGUE_GAMES
            games[j][i] = INTERLEAGUE_GAMES
    return games


def out_path(name: str) -> Path:
    return OUTPUT_DIR / name


def write_rating_csvs(
    date_updates: dict[str, list[tuple[str, float]]],
    teamdict: dict[str, int],
) -> None:
    """日次レーティングCSVを書き出す。"""
    teams = [Player(name) for name in TEAMNAMES]
    opening_before_day = (
        datetime.datetime.strptime(min(date_updates), "%Y-%m-%d")
        - datetime.timedelta(days=1)
    ).strftime("%Y-%m-%d")

    with (
        open(out_path("rating.csv"), "w", encoding="utf-8", newline="") as f_all,
        open(out_path("rating_central.csv"), "w", encoding="utf-8", newline="") as f_ce,
        open(out_path("rating_pacific.csv"), "w", encoding="utf-8", newline="") as f_pa,
    ):
        f_all.write("date," + ",".join(TEAMNAMES) + "\n")
        f_ce.write("date," + ",".join(CENTRAL) + "\n")
        f_pa.write("date," + ",".join(PACIFIC) + "\n")

        initial = f"{INITIAL_RATING:.2f}"
        f_all.write(opening_before_day + "," + ",".join([initial] * 12) + "\n")
        f_ce.write(opening_before_day + "," + ",".join([initial] * 6) + "\n")
        f_pa.write(opening_before_day + "," + ",".join([initial] * 6) + "\n")

        for day, updates in sorted(date_updates.items()):
            for teamname, rating in updates:
                teams[teamdict[teamname]].rating = rating
            ratings = [f"{t.rating:.2f}" for t in teams]
            f_all.write(",".join((day, *ratings)) + "\n")
            f_ce.write(",".join((day, *ratings[:6])) + "\n")
            f_pa.write(",".join((day, *ratings[6:])) + "\n")


def games_behind(leader_wins: int, leader_losses: int, wins: int, losses: int) -> float:
    return (leader_wins - wins + (losses - leader_losses)) / 2


def pennant_magic(leader_wins: int, chaser_wins: int, chaser_remaining: int) -> int:
    return chaser_remaining - (leader_wins - chaser_wins) + 1


def league_standings_meta(
    scores: list[list[int]],
    games_remain: list[list[int]],
    h2h: list[list[int]],
    prev_ranks: list[int],
    offset: int,
    *,
    central: bool,
) -> dict[str, tuple[str, str]]:
    """チーム名 -> (ゲーム差, マジック表示)."""
    order = rank_league(h2h, prev_ranks, offset, central=central)
    if not order:
        return {}

    leader_i = order[0]
    leader_wins, leader_losses, _ = scores[leader_i]
    leader_pct = win_pct(leader_wins, leader_losses)
    meta: dict[str, tuple[str, str]] = {TEAMNAMES[leader_i]: ("―", "")}
    for team_i in order[1:]:
        wins, losses, _draws = scores[team_i]
        gb = games_behind(leader_wins, leader_losses, wins, losses)
        meta[TEAMNAMES[team_i]] = (f"{gb:.1f}", "")

    second_i = order[1]
    second_pct = win_pct(scores[second_i][0], scores[second_i][1])
    if leader_pct > second_pct:
        magic = max(
            pennant_magic(
                leader_wins,
                scores[team_i][0],
                sum(games_remain[team_i]),
            )
            for team_i in order[1:]
        )
        if magic <= 0:
            meta[TEAMNAMES[leader_i]] = ("優勝", "優勝")
        elif magic <= sum(games_remain[leader_i]):
            meta[TEAMNAMES[leader_i]] = (f"M{magic}", f"M{magic}")

    return meta


def write_standings(
    scores: list[list[int]],
    games_remain: list[list[int]],
    h2h: list[list[int]],
    prev_ranks: list[int],
) -> None:
    meta = {}
    meta.update(
        league_standings_meta(scores, games_remain, h2h, prev_ranks, 0, central=True)
    )
    meta.update(
        league_standings_meta(scores, games_remain, h2h, prev_ranks, 6, central=False)
    )

    with open(out_path("standings.csv"), "w", encoding="utf-8", newline="") as f:
        f.write(
            "チーム名,勝,敗,分,勝率,ゲーム差,残,マジック,前年,"
            + ",".join(TEAMNAMES)
            + "\n"
        )
        for i, name in enumerate(TEAMNAMES):
            wins, losses, draws = scores[i]
            gb, magic = meta[name]
            remaining = sum(games_remain[i])
            f.write(
                ",".join(
                    map(
                        str,
                        [
                            name,
                            wins,
                            losses,
                            draws,
                            format_win_pct(wins, losses),
                            gb,
                            remaining,
                            magic,
                            prev_ranks[i],
                            *games_remain[i],
                        ],
                    )
                )
                + "\n"
            )


def write_h2h(h2h: list[list[int]]) -> None:
    with open(out_path("h2h.csv"), "w", encoding="utf-8", newline="") as f:
        f.write("チーム名," + ",".join(TEAMNAMES) + "\n")
        for i, name in enumerate(TEAMNAMES):
            f.write(",".join([name, *map(str, h2h[i])]) + "\n")


def write_win_probs(teams: list[Player]) -> list[list[float]]:
    win_prob = [[0.5] * 12 for _ in range(12)]
    for i in range(12):
        for j in range(i + 1, 12):
            p = teams[i].win_proba(teams[j])
            win_prob[i][j] = p
            win_prob[j][i] = 1.0 - p

    with open(out_path("win_prob.csv"), "w", encoding="utf-8", newline="") as f:
        f.write("チーム名,レーティング," + ",".join(TEAMNAMES) + "\n")
        for i, row in enumerate(win_prob):
            f.write(
                ",".join(
                    [TEAMNAMES[i], f"{teams[i].rating:.2f}"]
                    + [
                        "―" if i == j else f"{x * 100:.2f}"
                        for j, x in enumerate(row)
                    ]
                )
                + "\n"
            )
    return win_prob


def write_expected_standings(
    scores: list[list[int]],
    games_remain: list[list[int]],
    win_prob: list[list[float]],
) -> None:
    expected = [row[:] for row in scores]
    for i in range(12):
        for j in range(12):
            if i == j:
                continue
            n = games_remain[i][j]
            expected[i][0] += n * win_prob[i][j]
            expected[i][1] += n * win_prob[j][i]

    header = "チーム名,期待勝数,期待敗数,分,期待勝率\n"
    with (
        open(
            out_path("standings_estimate_central.csv"),
            "w",
            encoding="utf-8",
            newline="",
        ) as f_ce,
        open(
            out_path("standings_estimate_pacific.csv"),
            "w",
            encoding="utf-8",
            newline="",
        ) as f_pa,
    ):
        f_ce.write(header)
        f_pa.write(header)
        for i in range(6):
            for offset, out in ((0, f_ce), (6, f_pa)):
                idx = i + offset
                wins, losses, draws = expected[idx]
                out.write(
                    f"{TEAMNAMES[idx]},{wins:.2f},{losses:.2f},{draws},{format_win_pct(wins, losses)}\n"
                )


def remaining_matchups(
    games_remain: list[list[int]], win_prob: list[list[float]]
) -> list[tuple[int, int, int, float]]:
    return [
        (i, j, games_remain[i][j], win_prob[i][j])
        for i in range(12)
        for j in range(i + 1, 12)
        if games_remain[i][j] > 0
    ]


def _sim_binary() -> Path:
    root = Path(__file__).resolve().parent.parent
    name = "npb_sim.exe" if os.name == "nt" else "npb_sim"
    return root / "sim" / "target" / "release" / name


def _ensure_rust_sim() -> Path | None:
    """Release ビルド済みのシミュレーションバイナリを返す。必要なら cargo で作る。"""
    root = Path(__file__).resolve().parent.parent
    manifest = root / "sim" / "Cargo.toml"
    src = root / "sim" / "src" / "main.rs"
    if not manifest.exists() or not src.exists():
        return None
    exe = _sim_binary()
    newest_src = max(manifest.stat().st_mtime, src.stat().st_mtime)
    if exe.exists() and exe.stat().st_mtime >= newest_src:
        return exe
    env = os.environ.copy()
    env["CARGO_TARGET_DIR"] = str(root / "sim" / "target")
    cargo = subprocess.run(
        ["cargo", "build", "--release", "--manifest-path", str(manifest)],
        capture_output=True,
        text=True,
        env=env,
    )
    if cargo.returncode != 0:
        print(cargo.stderr, file=sys.stderr)
        print("Rustシミュレーションのビルドに失敗したため、Python実装を使います。", file=sys.stderr)
        return None
    return exe if exe.exists() else None


def simulate_ranks_python(
    h2h: list[list[int]],
    prev_ranks: list[int],
    matchups: list[tuple[int, int, int, float]],
    count: int,
) -> list[list[int]]:
    ranks = [[0] * 6 for _ in range(12)]
    for _ in range(count):
        sim_h2h = [row[:] for row in h2h]
        for i, j, n, p in matchups:
            for _game in range(n):
                if RNG.random() < p:
                    sim_h2h[i][j] += 1
                else:
                    sim_h2h[j][i] += 1

        central = rank_league(sim_h2h, prev_ranks, 0, central=True)
        pacific = rank_league(sim_h2h, prev_ranks, 6, central=False)
        for place in range(6):
            ranks[central[place]][place] += 1
            ranks[pacific[place]][place] += 1
    return ranks


def simulate_ranks_rust(
    h2h: list[list[int]],
    prev_ranks: list[int],
    matchups: list[tuple[int, int, int, float]],
    count: int,
    exe: Path,
) -> list[list[int]]:
    payload = {
        "h2h": h2h,
        "prev_ranks": prev_ranks,
        "matchups": matchups,
        "count": count,
        "seed": 10,
    }
    result = subprocess.run(
        [str(exe)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    ranks = json.loads(result.stdout)["ranks"]
    return [list(map(int, row)) for row in ranks]


def simulate_ranks(
    h2h: list[list[int]],
    prev_ranks: list[int],
    matchups: list[tuple[int, int, int, float]],
    count: int,
) -> list[list[int]]:
    """残り試合を現状の対戦勝率で抽選する。レーティングは試合ごとに更新しない。"""
    exe = _ensure_rust_sim()
    if exe is not None:
        try:
            ranks = simulate_ranks_rust(h2h, prev_ranks, matchups, count, exe)
            print(f"順位シミュレーション: Rust {count} 回")
            return ranks
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as exc:
            print(f"Rustシミュレーションに失敗したため Python に切り替えます: {exc}", file=sys.stderr)
    print(f"順位シミュレーション: Python {count} 回")
    return simulate_ranks_python(h2h, prev_ranks, matchups, count)


def write_victory_probs(ranks: list[list[int]], count: int) -> None:
    header = "チーム名," + ",".join(f"{x}位" for x in range(1, 7)) + "\n"
    with (
        open(
            out_path("victory_prob_central.csv"), "w", encoding="utf-8", newline=""
        ) as f_ce,
        open(
            out_path("victory_prob_pacific.csv"), "w", encoding="utf-8", newline=""
        ) as f_pa,
    ):
        f_ce.write(header)
        f_pa.write(header)
        for i, row in enumerate(ranks[:6]):
            f_ce.write(
                ",".join([TEAMNAMES[i]] + [f"{x / count * 100:.2f}" for x in row])
                + "\n"
            )
        for i, row in enumerate(ranks[6:]):
            f_pa.write(
                ",".join([TEAMNAMES[i + 6]] + [f"{x / count * 100:.2f}" for x in row])
                + "\n"
            )


def write_meta(year: int, prev_ranks: list[int]) -> None:
    payload = {
        "year": year,
        "isPreviousSeason": year < datetime.date.today().year,
        "prevRanks": {name: prev_ranks[i] for i, name in enumerate(TEAMNAMES)},
    }
    (OUTPUT_DIR / "meta.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_completed_games(path: Path) -> list[tuple[str, str, str, str, str]]:
    games: list[tuple[str, str, str, str, str]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split(",")
            if len(parts) != 5:
                continue
            date, ateam, ascore, bteam, bscore = parts
            if not ascore.isdigit() or not bscore.isdigit():
                continue
            games.append((date, ateam, ascore, bteam, bscore))
    games.sort(key=lambda game: game[0])
    return games


def apply_games(
    games: list[tuple[str, str, str, str, str]],
) -> tuple[
    list[list[int]],
    list[list[int]],
    list[list[int]],
    dict[str, Player],
    dict[str, int],
    dict[str, list[tuple[str, float]]],
]:
    scores: list[list[int]] = [[0, 0, 0] for _ in range(12)]
    games_remain = initial_games_remain()
    h2h = [[0] * 12 for _ in range(12)]
    teams_dict: dict[str, Player] = {name: Player(name) for name in TEAMNAMES}
    teamdict: dict[str, int] = {name: i for i, name in enumerate(TEAMNAMES)}
    date_updates: defaultdict[str, list[tuple[str, float]]] = defaultdict(list)

    for date, ateam, ascore, bteam, bscore in games:
        if ateam not in teamdict or bteam not in teamdict:
            continue

        ia, ib = teamdict[ateam], teamdict[bteam]
        if ascore == bscore:
            teams_dict[ateam], teams_dict[bteam] = update_rating_draw(
                teams_dict[ateam], teams_dict[bteam]
            )
            scores[ia][2] += 1
            scores[ib][2] += 1
        else:
            winner, loser = (
                (ateam, bteam) if int(ascore) > int(bscore) else (bteam, ateam)
            )
            teams_dict[winner], teams_dict[loser] = update_rating(
                teams_dict[winner], teams_dict[loser]
            )
            scores[teamdict[winner]][0] += 1
            scores[teamdict[loser]][1] += 1
            h2h[teamdict[winner]][teamdict[loser]] += 1

        date_updates[date].append((ateam, teams_dict[ateam].rating))
        date_updates[date].append((bteam, teams_dict[bteam].rating))
        games_remain[ia][ib] = max(0, games_remain[ia][ib] - 1)
        games_remain[ib][ia] = max(0, games_remain[ib][ia] - 1)

    return scores, games_remain, h2h, teams_dict, teamdict, date_updates


def compute_year(year: int, *, allow_fallback: bool = False) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scores_file = scores_path(year)
    if not scores_file.exists() or not has_completed_games(year):
        prev = year - 1
        if allow_fallback and has_completed_games(prev):
            print(f"{year}年の試合がないため、{prev}年の結果を計算します。")
            compute_year(prev, allow_fallback=False)
            return
        raise FileNotFoundError(
            f"{scores_file} に試合結果がありません。先に python scripts/scrape.py --year {year} を実行してください。"
        )

    prev_ranks = load_prev_ranks(year)
    scores, games_remain, h2h, teams_dict, teamdict, date_updates = apply_games(
        load_completed_games(scores_file)
    )

    if not date_updates:
        prev = year - 1
        if allow_fallback and has_completed_games(prev):
            print(f"{year}年の試合がないため、{prev}年の結果を計算します。")
            compute_year(prev, allow_fallback=False)
            return
        raise ValueError(f"{year}年の試合結果がありません。")

    write_rating_csvs(date_updates, teamdict)
    teams = [teams_dict[name] for name in TEAMNAMES]
    rating_sum = sum(team.rating for team in teams)
    expected_sum = INITIAL_RATING * len(TEAMNAMES)
    if abs(rating_sum - expected_sum) > 1e-6:
        print(
            f"警告: レーティング合計が {rating_sum:.4f} で、初期値合計 {expected_sum:.1f} と一致しません。",
            file=sys.stderr,
        )
    write_standings(scores, games_remain, h2h, prev_ranks)
    write_h2h(h2h)
    win_prob = write_win_probs(teams)
    write_expected_standings(scores, games_remain, win_prob)

    matchups = remaining_matchups(games_remain, win_prob)
    ranks = simulate_ranks(h2h, prev_ranks, matchups, SIMULATION_COUNT)
    write_victory_probs(ranks, SIMULATION_COUNT)
    write_meta(year, prev_ranks)
    print(f"{year}年の結果を {OUTPUT_DIR} に書き出しました。")


def main() -> None:
    parser = argparse.ArgumentParser(description="レーティングと順位予想を計算する")
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="対象年度（省略時は開幕前なら前年度）",
    )
    args = parser.parse_args()
    compute_year(resolve_year(args.year), allow_fallback=args.year is None)


if __name__ == "__main__":
    main()
