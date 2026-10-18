import { describe, expect, it } from "vitest";
import {
  formatSimCount,
  indexForDate,
  isDecidedProbs,
  isHistoryPayload,
  leagueSnapshot,
  snapshotRows,
} from "./victoryProbs";

describe("formatSimCount", () => {
  it("uses Japanese 10万 for the default simulation count", () => {
    expect(formatSimCount(100000)).toBe("10万");
  });
});

const payload = {
  count: 1000,
  teams: ["神", "広", "デ", "巨", "ヤ", "中", "オ", "ロ", "ソ", "楽", "西", "日"],
  dates: ["2026-04-01", "2026-04-03"],
  probs: [
    [
      [40, 20, 15, 15, 5, 5],
      [20, 20, 20, 20, 10, 10],
      [10, 20, 20, 20, 20, 10],
      [10, 20, 15, 15, 20, 20],
      [10, 10, 15, 15, 25, 25],
      [10, 10, 15, 15, 20, 30],
      [50, 20, 10, 10, 5, 5],
      [20, 30, 20, 10, 10, 10],
      [10, 20, 30, 20, 10, 10],
      [10, 10, 20, 30, 20, 10],
      [5, 10, 10, 20, 30, 25],
      [5, 10, 10, 10, 25, 40],
    ],
    [
      [80, 10, 5, 3, 1, 1],
      [10, 40, 20, 15, 10, 5],
      [5, 20, 30, 20, 15, 10],
      [3, 15, 20, 30, 20, 12],
      [1, 10, 15, 20, 30, 24],
      [1, 5, 10, 12, 24, 48],
      [70, 15, 8, 4, 2, 1],
      [15, 40, 20, 15, 5, 5],
      [8, 20, 40, 20, 8, 4],
      [4, 15, 20, 30, 20, 11],
      [2, 5, 8, 20, 40, 25],
      [1, 5, 4, 11, 25, 54],
    ],
  ],
};

describe("snapshotRows", () => {
  it("formats a league snapshot as a csv-like table", () => {
    expect(snapshotRows([[12.3, 0]], ["神"])).toEqual([
      ["チーム名", "1位", "2位", "3位", "4位", "5位", "6位"],
      ["神", "12.30", "0.00"],
    ]);
  });
});

describe("leagueSnapshot", () => {
  it("slices central teams for the selected date", () => {
    const rows = leagueSnapshot(payload, 1, 0);
    expect(rows[1][0]).toBe("神");
    expect(rows[1][1]).toBe("80.00");
    expect(rows[7]).toBeUndefined();
  });
});

describe("indexForDate", () => {
  it("snaps to the last game date on or before the chosen day", () => {
    expect(indexForDate(payload.dates, "2026-04-02")).toBe(0);
    expect(indexForDate(payload.dates, "2026-04-03")).toBe(1);
    expect(indexForDate(payload.dates, "2026-03-01")).toBe(0);
  });
});

describe("isHistoryPayload", () => {
  it("rejects incomplete history files", () => {
    expect(isHistoryPayload(payload)).toBe(true);
    expect(isHistoryPayload({ dates: ["2026-04-01"], probs: [] })).toBe(false);
  });
});

describe("isDecidedProbs", () => {
  it("detects a locked regular-season standing", () => {
    const decided = Array.from({ length: 12 }, (_, index) => {
      const row = [0, 0, 0, 0, 0, 0];
      row[index % 6] = 100;
      return row;
    });
    expect(isDecidedProbs(decided)).toBe(true);
    expect(isDecidedProbs(payload.probs[1])).toBe(false);
  });
});
