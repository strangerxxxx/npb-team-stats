import { CENTRAL, PACIFIC } from "../constants";

export const LEAGUE_TEAMS = {
  all: null,
  central: CENTRAL,
  pacific: PACIFIC,
};

export function ratingYDomain(data, step = 50) {
  const allRatings = data.flatMap((row) =>
    Object.entries(row)
      .filter(([key]) => key !== "date")
      .map(([, value]) => Number(value))
      .filter((value) => Number.isFinite(value))
  );
  if (!allRatings.length) return [1400, 1600];
  const min = Math.floor(Math.min(...allRatings) / step) * step;
  const max = Math.ceil(Math.max(...allRatings) / step) * step;
  return [min, max];
}

export function seriesVisibility(keys, league) {
  const allowed = LEAGUE_TEAMS[league];
  return keys.map((key) => ({
    key,
    hidden: Boolean(allowed && !allowed.includes(key)),
  }));
}
