import { describe, expect, it } from "vitest";
import { CENTRAL, PACIFIC } from "../constants";
import { ratingYDomain, seriesVisibility } from "./ratingChart";

const ALL_TEAMS = [...CENTRAL, ...PACIFIC];

describe("ratingYDomain", () => {
  it("uses every team’s ratings, not just the visible league", () => {
    const data = [
      { date: "2026-03-26", ヤ: 1405.12, ソ: 1500, 神: 1500 },
      { date: "2026-08-30", ヤ: 1410, ソ: 1600.52, 神: 1549.86 },
    ];
    expect(ratingYDomain(data)).toEqual([1400, 1650]);
  });

  it("stays the same if Central-only or Pacific-only values are the extremes", () => {
    const data = [
      { date: "a", ヤ: 1405, 神: 1500, ソ: 1601, 楽: 1480 },
      { date: "b", ヤ: 1410, 神: 1549, ソ: 1590, 楽: 1475 },
    ];
    const domain = ratingYDomain(data);
    const withoutPacific = ratingYDomain(
      data.map(({ ソ, 楽, ...row }) => row)
    );
    const withoutCentral = ratingYDomain(
      data.map(({ ヤ, 神, ...row }) => row)
    );
    expect(domain).toEqual([1400, 1650]);
    expect(withoutPacific).not.toEqual(domain);
    expect(withoutCentral).not.toEqual(domain);
  });

  it("returns a fallback domain when there is no numeric data", () => {
    expect(ratingYDomain([])).toEqual([1400, 1600]);
    expect(ratingYDomain([{ date: "2026-03-26" }])).toEqual([1400, 1600]);
  });
});

describe("seriesVisibility", () => {
  it("keeps a stable key order for every league so lines are not remounted", () => {
    const all = seriesVisibility(ALL_TEAMS, "all");
    const central = seriesVisibility(ALL_TEAMS, "central");
    const pacific = seriesVisibility(ALL_TEAMS, "pacific");
    expect(all.map((item) => item.key)).toEqual(ALL_TEAMS);
    expect(central.map((item) => item.key)).toEqual(ALL_TEAMS);
    expect(pacific.map((item) => item.key)).toEqual(ALL_TEAMS);
  });

  it("hides the other league’s teams", () => {
    const central = seriesVisibility(ALL_TEAMS, "central");
    const pacific = seriesVisibility(ALL_TEAMS, "pacific");
    expect(central.filter((item) => !item.hidden).map((item) => item.key)).toEqual(
      CENTRAL
    );
    expect(pacific.filter((item) => !item.hidden).map((item) => item.key)).toEqual(
      PACIFIC
    );
    expect(seriesVisibility(ALL_TEAMS, "all").every((item) => !item.hidden)).toBe(
      true
    );
  });
});
