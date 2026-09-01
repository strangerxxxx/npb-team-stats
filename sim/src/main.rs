use rand::Rng;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
struct Input {
    h2h: Vec<Vec<i32>>,
    prev_ranks: Vec<i32>,
    matchups: Vec<(usize, usize, u32, f64)>,
    count: u32,
    seed: u64,
}

#[derive(Serialize)]
struct Output {
    ranks: Vec<Vec<u32>>,
}

#[derive(Clone, Copy)]
enum Step {
    Overall,
    Wins,
    HeadToHead,
    Intra,
    PrevYear,
}

fn win_pct(wins: i32, losses: i32) -> f64 {
    let decided = wins + losses;
    if decided == 0 {
        0.0
    } else {
        wins as f64 / decided as f64
    }
}

fn same_key(a: f64, b: f64) -> bool {
    (a - b).abs() < 1e-12
}

fn overall_wl(h2h: &[[i32; 12]; 12], team: usize) -> (i32, i32) {
    let wins: i32 = h2h[team].iter().sum();
    let losses: i32 = (0..12).map(|opp| h2h[opp][team]).sum();
    (wins, losses)
}

fn h2h_wl(h2h: &[[i32; 12]; 12], team: usize, others: &[usize]) -> (i32, i32) {
    let mut wins = 0;
    let mut losses = 0;
    for &opp in others {
        if opp != team {
            wins += h2h[team][opp];
            losses += h2h[opp][team];
        }
    }
    (wins, losses)
}

fn step_key(
    step: Step,
    team: usize,
    group: &[usize],
    h2h: &[[i32; 12]; 12],
    prev_ranks: &[i32; 12],
    offset: usize,
) -> f64 {
    match step {
        Step::Overall => {
            let (w, l) = overall_wl(h2h, team);
            win_pct(w, l)
        }
        Step::Wins => h2h[team].iter().sum::<i32>() as f64,
        Step::HeadToHead => {
            let (w, l) = h2h_wl(h2h, team, group);
            win_pct(w, l)
        }
        Step::Intra => {
            let league = [offset, offset + 1, offset + 2, offset + 3, offset + 4, offset + 5];
            let (w, l) = h2h_wl(h2h, team, &league);
            win_pct(w, l)
        }
        Step::PrevYear => -(prev_ranks[team] as f64),
    }
}

fn break_ties(
    indices: &[usize],
    steps: &[Step],
    h2h: &[[i32; 12]; 12],
    prev_ranks: &[i32; 12],
    offset: usize,
) -> Vec<usize> {
    if indices.len() <= 1 || steps.is_empty() {
        return indices.to_vec();
    }
    let step = steps[0];
    let mut keyed: Vec<(f64, usize)> = indices
        .iter()
        .map(|&team| (step_key(step, team, indices, h2h, prev_ranks, offset), team))
        .collect();
    keyed.sort_by(|a, b| {
        b.0.partial_cmp(&a.0)
            .unwrap_or(std::cmp::Ordering::Equal)
            .then_with(|| a.1.cmp(&b.1))
    });
    if steps.len() == 1 {
        return keyed.into_iter().map(|(_, team)| team).collect();
    }
    let mut out = Vec::with_capacity(keyed.len());
    let mut start = 0;
    while start < keyed.len() {
        let mut end = start + 1;
        while end < keyed.len() && same_key(keyed[end].0, keyed[start].0) {
            end += 1;
        }
        let group: Vec<usize> = keyed[start..end].iter().map(|(_, team)| *team).collect();
        if group.len() == 1 {
            out.extend(group);
        } else {
            out.extend(break_ties(&group, &steps[1..], h2h, prev_ranks, offset));
        }
        start = end;
    }
    out
}

fn rank_league(
    h2h: &[[i32; 12]; 12],
    prev_ranks: &[i32; 12],
    offset: usize,
    central: bool,
) -> [usize; 6] {
    let league = [offset, offset + 1, offset + 2, offset + 3, offset + 4, offset + 5];
    let steps: &[Step] = if central {
        &[
            Step::Overall,
            Step::Wins,
            Step::HeadToHead,
            Step::Intra,
            Step::PrevYear,
        ]
    } else {
        &[
            Step::Overall,
            Step::HeadToHead,
            Step::Intra,
            Step::PrevYear,
        ]
    };
    let order = break_ties(&league, steps, h2h, prev_ranks, offset);
    let mut out = [0usize; 6];
    for (place, team) in order.into_iter().enumerate() {
        out[place] = team;
    }
    out
}

fn to_h2h_matrix(raw: &[Vec<i32>]) -> [[i32; 12]; 12] {
    let mut h2h = [[0i32; 12]; 12];
    for (i, row) in raw.iter().enumerate().take(12) {
        for (j, val) in row.iter().enumerate().take(12) {
            h2h[i][j] = *val;
        }
    }
    h2h
}

fn simulate_one(
    rng: &mut impl Rng,
    base_h2h: &[[i32; 12]; 12],
    prev_ranks: &[i32; 12],
    matchups: &[(usize, usize, u32, f64)],
    ranks: &mut [[u32; 6]; 12],
) {
    let mut h2h = *base_h2h;
    for &(i, j, n, p) in matchups {
        if i >= 12 || j >= 12 || i == j {
            continue;
        }
        let p = p.clamp(0.0, 1.0);
        for _ in 0..n {
            if rng.gen::<f64>() < p {
                h2h[i][j] += 1;
            } else {
                h2h[j][i] += 1;
            }
        }
    }

    let central = rank_league(&h2h, prev_ranks, 0, true);
    let pacific = rank_league(&h2h, prev_ranks, 6, false);
    for place in 0..6 {
        ranks[central[place]][place] += 1;
        ranks[pacific[place]][place] += 1;
    }
}

fn simulate(input: &Input) -> [[u32; 6]; 12] {
    let base_h2h = to_h2h_matrix(&input.h2h);
    let mut prev = [99i32; 12];
    for (i, rank) in input.prev_ranks.iter().enumerate().take(12) {
        prev[i] = *rank;
    }
    (0..input.count)
        .into_par_iter()
        .fold(
            || [[0u32; 6]; 12],
            |mut local, trial| {
                let mut rng = ChaCha8Rng::seed_from_u64(input.seed.wrapping_add(trial as u64));
                simulate_one(&mut rng, &base_h2h, &prev, &input.matchups, &mut local);
                local
            },
        )
        .reduce(
            || [[0u32; 6]; 12],
            |mut a, b| {
                for i in 0..12 {
                    for place in 0..6 {
                        a[i][place] += b[i][place];
                    }
                }
                a
            },
        )
}

fn main() {
    let input: Input =
        serde_json::from_reader(std::io::stdin().lock()).expect("invalid JSON input");
    if input.h2h.len() != 12 || input.h2h.iter().any(|row| row.len() != 12) {
        panic!("h2h must be 12x12");
    }
    if input.prev_ranks.len() != 12 {
        panic!("prev_ranks must have 12 teams");
    }
    let ranks = simulate(&input);
    let output = Output {
        ranks: ranks.iter().map(|row| row.to_vec()).collect(),
    };
    serde_json::to_writer(std::io::stdout().lock(), &output).expect("failed to write JSON");
}
