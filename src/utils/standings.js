import { CENTRAL, PACIFIC, isTeamAbbr } from "../constants";

export function winPct(wins, losses) {
  const decided = wins + losses;
  return decided ? wins / decided : 0;
}

export function formatWinPct(wins, losses) {
  const pct = winPct(wins, losses);
  if (pct >= 1) return "1.000";
  return `.${pct.toFixed(3).slice(2)}`;
}

export function formatGamesBehind(gb, isLeader) {
  if (isLeader) return "―";
  return gb.toFixed(1);
}

export function standingsRowClass(placeIndex, team) {
  if (team?.isLeader || placeIndex === 0) return "standings-leader";
  if (team?.rank != null ? team.rank <= 3 : placeIndex <= 2) {
    return "standings-cs";
  }
  return undefined;
}

export function gamesBehind(leader, team) {
  return (leader.wins - team.wins + (team.losses - leader.losses)) / 2;
}

function remainingFromRow(row, teamKeys) {
  return teamKeys.reduce((sum, key) => sum + (Number(row[key]) || 0), 0);
}

function sameKey(a, b) {
  if (Number.isInteger(a) && Number.isInteger(b)) return a === b;
  return Math.abs(a - b) < 1e-12;
}

function h2hRecord(h2h, team, others) {
  let wins = 0;
  let losses = 0;
  for (const opp of others) {
    if (opp === team) continue;
    wins += h2h[team]?.[opp] || 0;
    losses += h2h[opp]?.[team] || 0;
  }
  return [wins, losses];
}

function breakTies(indices, keyFn, rest) {
  if (indices.length <= 1) return [...indices];
  const keys = Object.fromEntries(
    indices.map((item) => [item, keyFn(item, indices)])
  );
  const ordered = [...indices].sort((a, b) => keys[b] - keys[a]);
  if (!rest.length) return ordered;

  const out = [];
  let start = 0;
  while (start < ordered.length) {
    let end = start + 1;
    while (end < ordered.length && sameKey(keys[ordered[end]], keys[ordered[start]])) {
      end += 1;
    }
    const group = ordered.slice(start, end);
    if (group.length === 1 || !rest.length) {
      out.push(...group);
    } else {
      out.push(...breakTies(group, rest[0], rest.slice(1)));
    }
    start = end;
  }
  return out;
}

function sortTeams(teams, h2h, prevRanks, central) {
  if (teams.length === 0) return teams;
  const byAbbr = Object.fromEntries(teams.map((team) => [team.abbr, team]));
  const league = teams.map((team) => team.abbr);

  const overallPct = (abbr) => byAbbr[abbr].pct;
  const winsKey = (abbr) => byAbbr[abbr].wins;
  const h2hPct = (abbr, group) => {
    const [wins, losses] = h2hRecord(h2h, abbr, group);
    return winPct(wins, losses);
  };
  const intraPct = (abbr) => {
    const [wins, losses] = h2hRecord(h2h, abbr, league);
    return winPct(wins, losses);
  };
  const prevKey = (abbr) => -(prevRanks[abbr] ?? 99);

  const steps = central
    ? [overallPct, winsKey, h2hPct, intraPct, prevKey]
    : [overallPct, h2hPct, intraPct, prevKey];
  const order = breakTies(league, steps[0], steps.slice(1));
  return order.map((abbr) => byAbbr[abbr]);
}

function magicNumber(leader, chaser) {
  return chaser.remaining - (leader.wins - chaser.wins) + 1;
}

function attachStandingsFields(teams, h2h, prevRanks, central) {
  const ranked = sortTeams(teams, h2h, prevRanks, central);
  if (ranked.length === 0) return ranked;

  const leader = ranked[0];
  ranked.forEach((team, index) => {
    team.rank = index + 1;
    team.isLeader = index === 0;
    team.gb = gamesBehind(leader, team);
    team.magic = "";
  });

  const second = ranked[1];
  if (second && leader.pct > second.pct) {
    const pennant = Math.max(
      ...ranked.slice(1).map((team) => magicNumber(leader, team))
    );
    if (pennant <= 0) {
      leader.magic = "優勝";
    } else if (pennant <= leader.remaining) {
      leader.magic = `M${pennant}`;
    }
  }

  return ranked;
}

export function parseH2h(rows) {
  const matrix = {};
  for (const row of rows || []) {
    const team = row.チーム名;
    if (!team) continue;
    matrix[team] = {};
    for (const key of Object.keys(row)) {
      if (isTeamAbbr(key)) matrix[team][key] = Number(row[key]) || 0;
    }
  }
  return matrix;
}

export function buildLeagueStandings(
  rows,
  leagueTeams,
  otherLeague,
  h2h,
  prevRanks,
  central
) {
  const teamKeys = Object.keys(rows[0] || {}).filter(isTeamAbbr);
  const leagueSet = new Set(leagueTeams);

  const teams = rows
    .filter((row) => leagueSet.has(row.チーム名))
    .map((row) => {
      const wins = Number(row.勝);
      const losses = Number(row.敗);
      const draws = Number(row.分);
      return {
        abbr: row.チーム名,
        wins,
        losses,
        draws,
        games: wins + losses + draws,
        pct: winPct(wins, losses),
        remaining: remainingFromRow(row, teamKeys),
        remainInterleague: otherLeague.reduce(
          (sum, name) => sum + (Number(row[name]) || 0),
          0
        ),
        remainVs: Object.fromEntries(
          leagueTeams.map((name) => [name, Number(row[name]) || 0])
        ),
      };
    });

  return attachStandingsFields(teams, h2h, prevRanks, central);
}

export function splitStandings(rows, h2hRows, prevRanks = {}) {
  const h2h = parseH2h(h2hRows);
  return {
    central: buildLeagueStandings(
      rows,
      CENTRAL,
      PACIFIC,
      h2h,
      prevRanks,
      true
    ),
    pacific: buildLeagueStandings(
      rows,
      PACIFIC,
      CENTRAL,
      h2h,
      prevRanks,
      false
    ),
  };
}
