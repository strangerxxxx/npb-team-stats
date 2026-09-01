import { isTeamAbbr } from "../constants";

export function reorderTable(headers, body, teamOrder) {
  if (!teamOrder?.length || body.length === 0) {
    return [headers, ...body];
  }

  const rank = new Map(teamOrder.map((abbr, index) => [abbr, index]));
  const sortedBody = [...body].sort((a, b) => {
    const aRank = rank.has(a[0]) ? rank.get(a[0]) : 999;
    const bRank = rank.has(b[0]) ? rank.get(b[0]) : 999;
    return aRank - bRank;
  });

  const teamCols = teamOrder
    .map((abbr) => headers.indexOf(abbr))
    .filter((index) => index > 0);
  if (teamCols.length === 0) {
    return [headers, ...sortedBody];
  }

  const otherCols = headers
    .map((_, index) => index)
    .filter((index) => index === 0 || !isTeamAbbr(headers[index]));
  const colOrder = [...otherCols, ...teamCols.filter((index) => index !== 0)];
  const unique = [...new Set(colOrder)];

  return [
    unique.map((index) => headers[index]),
    ...sortedBody.map((row) => unique.map((index) => row[index])),
  ];
}
