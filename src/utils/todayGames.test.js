import { describe, expect, it } from "vitest";
import {
  formatGameDate,
  formatRating,
  formatRatingDelta,
  formatWinPct,
  statusText,
} from "./todayGames";

describe("formatRating", () => {
  it("formats ratings to two decimals", () => {
    expect(formatRating(1543.371)).toBe("1543.37");
    expect(formatRating(null)).toBe("");
  });
});

describe("formatWinPct", () => {
  it("formats NPB win pct as a percentage label", () => {
    expect(formatWinPct(".448")).toBe("勝率44.8%");
    expect(formatWinPct("1.000")).toBe("勝率100.0%");
    expect(formatWinPct(".000")).toBe("勝率0.0%");
    expect(formatWinPct(null)).toBe("");
  });
});
describe("formatRatingDelta", () => {
  it("adds a plus sign for gains", () => {
    expect(formatRatingDelta(8.12)).toBe("+8.12");
    expect(formatRatingDelta(-8)).toBe("-8.00");
    expect(formatRatingDelta(0)).toBe("0.00");
    expect(formatRatingDelta(null)).toBe("");
  });
});

describe("statusText", () => {
  it("prefers start time or inning when present", () => {
    expect(statusText({ status: "試合前", note: "18:00" })).toBe("18:00");
    expect(statusText({ status: "試合中", note: "5回表" })).toBe("5回表");
    expect(statusText({ status: "試合終了" })).toBe("試合終了");
  });
});

describe("formatGameDate", () => {
  it("formats ISO dates in Japanese", () => {
    expect(formatGameDate("2026-09-01")).toBe("9月1日");
  });
});
