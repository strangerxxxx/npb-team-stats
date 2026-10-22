import { CENTRAL, PACIFIC } from "../constants";

const SERIES_ORDER = [
  "クライマックスシリーズ|ファーストステージ|central",
  "クライマックスシリーズ|ファーストステージ|pacific",
  "クライマックスシリーズ|ファイナルステージ|central",
  "クライマックスシリーズ|ファイナルステージ|pacific",
  "日本シリーズ||",
];

export const FIRST_STAGE_WINS = 2;
export const FIRST_STAGE_GAMES = 3;
export const FINAL_STAGE_WINS = 4;
export const FINAL_STAGE_GAMES = 6;
export const FINAL_ADVANTAGE = 1;
export const FINAL_STAGE_WINS_EXTENDED = 5;
export const FINAL_STAGE_GAMES_EXTENDED = 7;
export const FINAL_ADVANTAGE_EXTENDED = 2;
export const JAPAN_SERIES_WINS = 4;
export const JAPAN_SERIES_GAMES = 7;
export const LARGE_GAME_DIFF = 10;

export function seriesGameLabel(game) {
  if (!game?.series) return "";
  const gameNo = game.game_no ? ` 第${game.game_no}戦` : "";
  if (game.series === "日本シリーズ") {
    return `日本シリーズ${gameNo}`.trim();
  }
  const stage = game.stage ? ` ${game.stage}` : "";
  return `${game.series}${stage}${gameNo}`.trim();
}

export function seriesHeading(group) {
  if (group.series === "日本シリーズ") return "日本シリーズ";
  const league = group.league === "central" ? "セ・リーグ" : "パ・リーグ";
  const stage = group.stage ? ` ${group.stage}` : "";
  return `${group.series} ${league}${stage}`;
}

export function groupPostseason(games) {
  const groups = [];
  const index = new Map();
  for (const game of games || []) {
    if (!game.series) continue;
    const key = `${game.series}|${game.stage || ""}|${game.league || ""}`;
    if (!index.has(key)) {
      const group = {
        series: game.series,
        stage: game.stage || "",
        league: game.league || "",
        games: [],
      };
      index.set(key, group);
      groups.push(group);
    }
    index.get(key).games.push(game);
  }
  for (const group of groups) {
    group.games.sort((left, right) => {
      const byDate = String(left.date || "").localeCompare(String(right.date || ""));
      if (byDate !== 0) return byDate;
      return (left.game_no || 0) - (right.game_no || 0);
    });
  }
  return groups.sort((left, right) => {
    const leftKey = `${left.series}|${left.stage}|${left.league}`;
    const rightKey = `${right.series}|${right.stage}|${right.league}`;
    const leftRank = SERIES_ORDER.indexOf(leftKey);
    const rightRank = SERIES_ORDER.indexOf(rightKey);
    return (leftRank < 0 ? 99 : leftRank) - (rightRank < 0 ? 99 : rightRank);
  });
}

export function seriesWins(games) {
  const wins = {};
  for (const game of games || []) {
    if (game.status !== "試合終了") continue;
    const aScore = Number(game.ascore);
    const bScore = Number(game.bscore);
    if (!Number.isFinite(aScore) || !Number.isFinite(bScore) || aScore === bScore) {
      continue;
    }
    const winner = aScore > bScore ? game.ateam : game.bteam;
    wins[winner] = (wins[winner] || 0) + 1;
  }
  return wins;
}

function findGroup(groups, series, stage, league) {
  return (
    groups.find(
      (group) =>
        group.series === series &&
        group.stage === stage &&
        group.league === league
    ) || { games: [] }
  );
}

function uniqueTeams(games) {
  const teams = [];
  for (const game of games || []) {
    for (const abbr of [game.ateam, game.bteam]) {
      if (abbr && !teams.includes(abbr)) teams.push(abbr);
    }
  }
  return teams;
}

function placeTeam(places, pool, place) {
  return pool.find((abbr) => places[abbr] === place) || null;
}

function otherTeam(games, known) {
  for (const abbr of uniqueTeams(games)) {
    if (abbr !== known) return abbr;
  }
  return null;
}

export function gamesBehind(leader, team) {
  if (!leader || !team) return 0;
  return (leader.wins - team.wins + (team.losses - leader.losses)) / 2;
}

export function winningPct(record) {
  const played = (record?.wins || 0) + (record?.losses || 0);
  return played ? record.wins / played : 0;
}

export function finalStageFormat(seed1, challenger, records = {}) {
  const leader = records[seed1];
  const other = records[challenger];
  if (leader && other) {
    const blowout = gamesBehind(leader, other) >= LARGE_GAME_DIFF;
    const under500 = winningPct(other) < 0.5;
    if (blowout || under500) {
      return {
        advantage: FINAL_ADVANTAGE_EXTENDED,
        target: FINAL_STAGE_WINS_EXTENDED,
        maxGames: FINAL_STAGE_GAMES_EXTENDED,
        note: "7試合制・5勝先取（1位に2勝のアドバンテージ）",
      };
    }
  }
  return {
    advantage: FINAL_ADVANTAGE,
    target: FINAL_STAGE_WINS,
    maxGames: FINAL_STAGE_GAMES,
    note: "6試合制・4勝先取（1位に1勝のアドバンテージ）",
  };
}

export function seriesDecision({
  higherSeed,
  lowerSeed,
  wins,
  advantage = 0,
  target,
  maxGames,
  games,
}) {
  if (!higherSeed || !lowerSeed) return null;
  const high = (wins[higherSeed] || 0) + advantage;
  const low = wins[lowerSeed] || 0;
  if (high >= target) return higherSeed;
  if (low >= target) return lowerSeed;
  const remaining = remainingGames(maxGames, games);
  if (high >= low + remaining) return higherSeed;
  if (low > high + remaining) return lowerSeed;
  return null;
}

export function remainingGames(maxGames, games) {
  const played = (games || []).filter((game) => game.status === "試合終了").length;
  return Math.max(0, (maxGames || 0) - played);
}

export function ratingsFromGames(games) {
  const ratings = {};
  for (const game of games || []) {
    const a = Number(game.a_rating);
    const b = Number(game.b_rating);
    if (game.ateam && Number.isFinite(a)) ratings[game.ateam] = a;
    if (game.bteam && Number.isFinite(b)) ratings[game.bteam] = b;
  }
  return ratings;
}

export function eloWinProb(ratingA, ratingB) {
  const a = Number(ratingA);
  const b = Number(ratingB);
  if (!Number.isFinite(a) || !Number.isFinite(b)) return null;
  return 1 / (1 + 10 ** ((b - a) / 400));
}

export function seriesWinProb({ gameProb, highWins, lowWins, remaining, target }) {
  if (gameProb == null || gameProb === "") return null;
  const p = Number(gameProb);
  if (!Number.isFinite(p) || remaining < 0 || target == null) return null;
  const memo = new Map();
  const dp = (high, low, left) => {
    const key = `${high}|${low}|${left}`;
    if (memo.has(key)) return memo.get(key);
    let value;
    if (high >= target) value = 1;
    else if (low >= target) value = 0;
    else if (left <= 0) value = high >= low ? 1 : 0;
    else if (high >= low + left) value = 1;
    else if (low > high + left) value = 0;
    else {
      value = p * dp(high + 1, low, left - 1) + (1 - p) * dp(high, low + 1, left - 1);
    }
    memo.set(key, value);
    return value;
  };
  return dp(highWins || 0, lowWins || 0, remaining);
}

export function formatSeriesProb(label, value) {
  if (!label || value == null || value === "") return "";
  const n = Number(value);
  if (!Number.isFinite(n)) return "";
  return `${label}${(n * 100).toFixed(1)}%`;
}

export function seriesProbText(match, abbr) {
  if (!match?.probLabel || match.winner || !abbr) return "";
  const row = (match.rows || []).find((item) => item.abbr === abbr);
  return formatSeriesProb(match.probLabel, row?.prob);
}

export function matchForGame(game, bracket) {
  if (!game?.series || !bracket) return null;
  if (game.series === "日本シリーズ") return bracket.japan || null;
  const league = (bracket.leagues || []).find((item) => item.id === game.league);
  if (!league) return null;
  if (game.stage === "ファーストステージ") return league.first;
  if (game.stage === "ファイナルステージ") return league.final;
  return null;
}

function withSeriesProbs(
  match,
  { higher, lower, ratings, remaining, target, highWins, lowWins, label }
) {
  if (!match.ready || match.winner || !higher || !lower) return match;
  const gameProb = eloWinProb(ratings?.[higher], ratings?.[lower]);
  const highProb = seriesWinProb({
    gameProb,
    highWins,
    lowWins,
    remaining,
    target,
  });
  if (highProb == null) return match;
  return {
    ...match,
    probLabel: label,
    rows: match.rows.map((row) => ({
      ...row,
      prob:
        row.abbr === higher ? highProb : row.abbr === lower ? 1 - highProb : null,
    })),
  };
}

function matchRow(abbr, { seed, wins, advantage = 0, isWinner = false }) {
  const total = (wins[abbr] || 0) + advantage;
  return {
    abbr,
    seed: seed || null,
    advantage,
    gameWins: wins[abbr] || 0,
    wins: total,
    isWinner,
  };
}

function makeMatch({ title, note, target, rows, winner }) {
  return {
    title,
    note,
    target,
    winner,
    rows: rows.map((row) => ({ ...row, isWinner: Boolean(row.abbr) && row.abbr === winner })),
    ready: rows.filter((row) => row.abbr).length === 2,
  };
}

function leagueBracket(groups, places, records, id, name, pool, ratings) {
  const firstGames = findGroup(
    groups,
    "クライマックスシリーズ",
    "ファーストステージ",
    id
  ).games;
  const finalGames = findGroup(
    groups,
    "クライマックスシリーズ",
    "ファイナルステージ",
    id
  ).games;
  const firstWins = seriesWins(firstGames);
  const finalWins = seriesWins(finalGames);
  const firstTeams = uniqueTeams(firstGames).sort(
    (left, right) => (places[left] || 99) - (places[right] || 99)
  );
  const seed2 = firstTeams[0] || placeTeam(places, pool, 2);
  const seed3 = firstTeams[1] || placeTeam(places, pool, 3);
  const firstWinner = seriesDecision({
    higherSeed: seed2,
    lowerSeed: seed3,
    wins: firstWins,
    target: FIRST_STAGE_WINS,
    maxGames: FIRST_STAGE_GAMES,
    games: firstGames,
  });
  const first = withSeriesProbs(
    makeMatch({
      title: "ファーストステージ",
      note: "3試合制・2勝先取（同勝なら2位）",
      target: FIRST_STAGE_WINS,
      winner: firstWinner,
      rows: [
        matchRow(seed2, {
          seed: seed2 ? places[seed2] || 2 : null,
          wins: firstWins,
        }),
        matchRow(seed3, {
          seed: seed3 ? places[seed3] || 3 : null,
          wins: firstWins,
        }),
      ],
    }),
    {
      higher: seed2,
      lower: seed3,
      ratings,
      remaining: remainingGames(FIRST_STAGE_GAMES, firstGames),
      target: FIRST_STAGE_WINS,
      highWins: firstWins[seed2] || 0,
      lowWins: firstWins[seed3] || 0,
      label: "突破率",
    }
  );
  const seed1 = placeTeam(places, pool, 1) || otherTeam(finalGames, first.winner);
  const challenger = first.winner || otherTeam(finalGames, seed1);
  const format = finalStageFormat(seed1, challenger, records);
  const advantage = seed1 ? format.advantage : 0;
  const finalWinner = seriesDecision({
    higherSeed: seed1,
    lowerSeed: challenger,
    wins: finalWins,
    advantage,
    target: format.target,
    maxGames: format.maxGames,
    games: finalGames,
  });
  return {
    id,
    name,
    first,
    final: withSeriesProbs(
      makeMatch({
        title: "ファイナルステージ",
        note: format.note,
        target: format.target,
        winner: finalWinner,
        rows: [
          matchRow(seed1, {
            seed: 1,
            wins: finalWins,
            advantage,
          }),
          matchRow(challenger, {
            seed: places[challenger] || null,
            wins: finalWins,
          }),
        ],
      }),
      {
        higher: seed1,
        lower: challenger,
        ratings,
        remaining: remainingGames(format.maxGames, finalGames),
        target: format.target,
        highWins: (finalWins[seed1] || 0) + advantage,
        lowWins: finalWins[challenger] || 0,
        label: "突破率",
      }
    ),
  };
}

export function buildBracket(seriesGames, places = {}, records = {}) {
  const groups = groupPostseason(seriesGames);
  if (!groups.length) return null;
  const ratings = ratingsFromGames(seriesGames);

  const leagues = [
    leagueBracket(groups, places, records, "central", "セ・リーグ", CENTRAL, ratings),
    leagueBracket(groups, places, records, "pacific", "パ・リーグ", PACIFIC, ratings),
  ];
  const japanGames = findGroup(groups, "日本シリーズ", "", "").games;
  const japanWins = seriesWins(japanGames);
  const japanTeams = uniqueTeams(japanGames);
  let home = leagues[0].final.winner;
  let away = leagues[1].final.winner;
  if (japanTeams.length === 2) {
    if (home && japanTeams.includes(home)) {
      away = japanTeams.find((abbr) => abbr !== home);
    } else {
      [home, away] = japanTeams;
    }
  }
  const japanWinner = seriesDecision({
    higherSeed: home,
    lowerSeed: away,
    wins: japanWins,
    target: JAPAN_SERIES_WINS,
    maxGames: JAPAN_SERIES_GAMES,
    games: japanGames,
  });
  return {
    leagues,
    japan: withSeriesProbs(
      makeMatch({
        title: "日本シリーズ",
        note: "7試合制・4勝先取",
        target: JAPAN_SERIES_WINS,
        winner: japanWinner,
        rows: [
          matchRow(home, { wins: japanWins }),
          matchRow(away, { wins: japanWins }),
        ],
      }),
      {
        higher: home,
        lower: away,
        ratings,
        remaining: remainingGames(JAPAN_SERIES_GAMES, japanGames),
        target: JAPAN_SERIES_WINS,
        highWins: japanWins[home] || 0,
        lowWins: japanWins[away] || 0,
        label: "優勝率",
      }
    ),
  };
}
