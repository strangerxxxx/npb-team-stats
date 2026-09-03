import { describe, expect, it } from "vitest";
import {
  formatGameDate,
  formatRatingDelta,
  statusText,
} from "./todayGames";

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
