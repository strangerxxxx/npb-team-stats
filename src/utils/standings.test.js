import { describe, expect, it } from "vitest";
import { CENTRAL, PACIFIC } from "../constants";
import {
  buildLeagueStandings,
  formatWinPct,
  standingsRowClass,
} from "./standings";

const PREV = Object.fromEntries(
  [...CENTRAL, ...PACIFIC].map((abbr, index) => [abbr, (index % 6) + 1])
);

function remainZeros() {
  return Object.fromEntries([...CENTRAL, ...PACIFIC].map((abbr) => [abbr, 0]));
}

function makeRows(records, league = CENTRAL) {
  return league.map((abbr) => {
    const { wins, losses } = records[abbr] ?? { wins: 0, losses: 10 };
    return {
      チーム名: abbr,
      勝: wins,
      敗: losses,
      分: 0,
      ...remainZeros(),
    };
  });
}

describe("standingsRowClass", () => {
  it("marks 1st gold and 2nd–3rd as CS", () => {
    expect(standingsRowClass(0)).toBe("standings-leader");
    expect(standingsRowClass(1)).toBe("standings-cs");
    expect(standingsRowClass(2)).toBe("standings-cs");
    expect(standingsRowClass(3)).toBeUndefined();
  });
});

describe("formatWinPct", () => {
  it("formats as .xxx", () => {
    expect(formatWinPct(67, 49)).toBe(".578");
    expect(formatWinPct(1, 0)).toBe("1.000");
  });
});

describe("buildLeagueStandings", () => {
  const tiedPct = {
    神: { wins: 20, losses: 20 },
    広: { wins: 10, losses: 10 },
    デ: { wins: 4, losses: 20 },
    巨: { wins: 3, losses: 20 },
    ヤ: { wins: 2, losses: 20 },
    中: { wins: 1, losses: 20 },
  };
  const h2hHiroshimaSeries = {
    神: { 広: 2 },
    広: { 神: 8 },
  };

  it("breaks a Central tie by win count before head-to-head", () => {
    const ranked = buildLeagueStandings(
      makeRows(tiedPct),
      CENTRAL,
      PACIFIC,
      h2hHiroshimaSeries,
      PREV,
      true
    );
    expect(ranked.map((team) => team.abbr).slice(0, 2)).toEqual(["神", "広"]);
  });

  it("breaks a Pacific tie by head-to-head, ignoring win count", () => {
    const ranked = buildLeagueStandings(
      makeRows(tiedPct),
      CENTRAL,
      PACIFIC,
      h2hHiroshimaSeries,
      PREV,
      false
    );
    expect(ranked.map((team) => team.abbr).slice(0, 2)).toEqual(["広", "神"]);
  });

  it("falls back to previous-year rank when records match", () => {
    const records = {
      神: { wins: 10, losses: 10 },
      広: { wins: 10, losses: 10 },
      デ: { wins: 4, losses: 20 },
      巨: { wins: 3, losses: 20 },
      ヤ: { wins: 2, losses: 20 },
      中: { wins: 1, losses: 20 },
    };
    const ranked = buildLeagueStandings(
      makeRows(records),
      CENTRAL,
      PACIFIC,
      {},
      { ...PREV, 神: 5, 広: 1 },
      true
    );
    expect(ranked[0].abbr).toBe("広");
    expect(ranked[1].abbr).toBe("神");
  });
});
