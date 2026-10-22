import { describe, expect, it } from "vitest";
import {
  buildBracket,
  eloWinProb,
  finalStageFormat,
  formatSeriesProb,
  groupPostseason,
  seriesDecision,
  seriesGameLabel,
  seriesHeading,
  seriesWinProb,
} from "./postseason";

describe("seriesGameLabel", () => {
  it("formats climax and japan series game labels", () => {
    expect(
      seriesGameLabel({
        series: "クライマックスシリーズ",
        stage: "ファイナルステージ",
        game_no: 4,
      })
    ).toBe("クライマックスシリーズ ファイナルステージ 第4戦");
    expect(seriesGameLabel({ series: "日本シリーズ", game_no: 1 })).toBe(
      "日本シリーズ 第1戦"
    );
    expect(seriesGameLabel({})).toBe("");
  });
});

describe("groupPostseason", () => {
  it("groups by series, stage, and league", () => {
    const groups = groupPostseason([
      {
        series: "日本シリーズ",
        stage: "",
        league: "",
        ateam: "デ",
      },
      {
        series: "クライマックスシリーズ",
        stage: "ファイナルステージ",
        league: "central",
        ateam: "神",
      },
      {
        series: "クライマックスシリーズ",
        stage: "ファーストステージ",
        league: "pacific",
        ateam: "西",
      },
    ]);
    expect(groups.map(seriesHeading)).toEqual([
      "クライマックスシリーズ パ・リーグ ファーストステージ",
      "クライマックスシリーズ セ・リーグ ファイナルステージ",
      "日本シリーズ",
    ]);
  });

  it("sorts games in a series by date", () => {
    const groups = groupPostseason([
      { series: "日本シリーズ", date: "2026-10-25", game_no: 2 },
      { series: "日本シリーズ", date: "2026-10-24", game_no: 1 },
    ]);
    expect(groups[0].games.map((game) => game.game_no)).toEqual([1, 2]);
  });
});

describe("buildBracket", () => {
  it("builds CS and Japan Series from games and regular-season places", () => {
    const games = [
      finished("巨", "デ", 1, 2, "ファーストステージ", "central"),
      finished("巨", "デ", 1, 4, "ファーストステージ", "central"),
      finished("西", "日", 3, 2, "ファーストステージ", "pacific"),
      finished("西", "日", 0, 1, "ファーストステージ", "pacific"),
      finished("西", "日", 1, 4, "ファーストステージ", "pacific"),
      finished("神", "デ", 0, 2, "ファイナルステージ", "central"),
      finished("神", "デ", 0, 1, "ファイナルステージ", "central"),
      finished("神", "デ", 0, 4, "ファイナルステージ", "central"),
      finished("神", "デ", 5, 8, "ファイナルステージ", "central"),
      finished("ソ", "日", 6, 4, "ファイナルステージ", "pacific"),
      finished("ソ", "日", 6, 2, "ファイナルステージ", "pacific"),
      finished("ソ", "日", 6, 2, "ファイナルステージ", "pacific"),
      {
        series: "日本シリーズ",
        stage: "",
        league: "",
        ateam: "デ",
        bteam: "ソ",
        ascore: null,
        bscore: null,
        status: "試合前",
      },
    ];
    const places = { 神: 1, 巨: 2, デ: 3, ソ: 1, 西: 2, 日: 3 };
    const records = {
      神: { wins: 79, losses: 62 },
      デ: { wins: 71, losses: 69 },
      ソ: { wins: 91, losses: 49 },
      日: { wins: 78, losses: 62 },
    };
    const bracket = buildBracket(games, places, records);
    expect(bracket.leagues[0].first.winner).toBe("デ");
    expect(bracket.leagues[0].first.rows.map((row) => row.wins)).toEqual([0, 2]);
    expect(bracket.leagues[0].final.note).toContain("6試合制");
    expect(bracket.leagues[0].final.winner).toBe("デ");
    expect(bracket.leagues[0].final.rows[0]).toMatchObject({
      abbr: "神",
      advantage: 1,
      wins: 1,
    });
    expect(bracket.leagues[0].final.rows[1]).toMatchObject({
      abbr: "デ",
      wins: 4,
      isWinner: true,
    });
    expect(bracket.leagues[1].first.winner).toBe("日");
    expect(bracket.leagues[1].final.note).toContain("7試合制");
    expect(bracket.leagues[1].final.winner).toBe("ソ");
    expect(bracket.leagues[1].final.rows[0]).toMatchObject({
      abbr: "ソ",
      advantage: 2,
      wins: 5,
    });
    expect(bracket.japan.rows.map((row) => row.abbr)).toEqual(["デ", "ソ"]);
    expect(bracket.japan.winner).toBeNull();
  });

  it("adds 突破率 to an undecided CS series and 優勝率 to an undecided Japan Series", () => {
    const games = [
      finished("巨", "デ", 1, 2, "ファーストステージ", "central"),
      {
        series: "クライマックスシリーズ",
        stage: "ファーストステージ",
        league: "central",
        ateam: "巨",
        bteam: "デ",
        ascore: null,
        bscore: null,
        status: "試合前",
        a_rating: 1540,
        b_rating: 1500,
      },
      {
        series: "日本シリーズ",
        stage: "",
        league: "",
        ateam: "デ",
        bteam: "ソ",
        status: "試合前",
        a_rating: 1575.13,
        b_rating: 1652.84,
      },
    ];
    const bracket = buildBracket(games, { 神: 1, 巨: 2, デ: 3, ソ: 1, 西: 2, 日: 3 });
    const first = bracket.leagues[0].first;
    expect(first.winner).toBeNull();
    expect(first.probLabel).toBe("突破率");
    expect(first.rows.map((row) => row.abbr)).toEqual(["巨", "デ"]);
    expect(first.rows[0].prob + first.rows[1].prob).toBeCloseTo(1);
    expect(first.rows[1].prob).toBeGreaterThan(first.rows[0].prob);
    expect(bracket.japan.probLabel).toBe("優勝率");
    expect(bracket.japan.rows.find((row) => row.abbr === "ソ").prob).toBeGreaterThan(
      bracket.japan.rows.find((row) => row.abbr === "デ").prob
    );
  });
});

describe("seriesDecision", () => {
  it("gives a tied first stage to the higher seed after 3 games", () => {
    expect(
      seriesDecision({
        higherSeed: "巨",
        lowerSeed: "デ",
        wins: { 巨: 1, デ: 1 },
        target: 2,
        maxGames: 3,
        games: [{ status: "試合終了" }, { status: "試合終了" }, { status: "試合終了" }],
      })
    ).toBe("巨");
  });

  it("ends the first stage when the 2nd-place team cannot be overtaken", () => {
    expect(
      seriesDecision({
        higherSeed: "巨",
        lowerSeed: "デ",
        wins: { 巨: 1, デ: 0 },
        target: 2,
        maxGames: 3,
        games: [{ status: "試合終了" }, { status: "試合終了" }],
      })
    ).toBe("巨");
  });
});

describe("seriesWinProb", () => {
  it("does not treat a missing game probability as zero", () => {
    expect(
      seriesWinProb({
        gameProb: null,
        highWins: 0,
        lowWins: 0,
        remaining: 3,
        target: 2,
      })
    ).toBeNull();
  });

  it("gives the higher seed a first-stage edge only through remaining games", () => {
    expect(
      seriesWinProb({
        gameProb: 0.6,
        highWins: 0,
        lowWins: 0,
        remaining: 3,
        target: 2,
      })
    ).toBeCloseTo(0.6 ** 2 * (3 - 2 * 0.6));
    expect(
      seriesWinProb({
        gameProb: 0.55,
        highWins: 1,
        lowWins: 1,
        remaining: 1,
        target: 2,
      })
    ).toBeCloseTo(0.55);
  });

  it("gives Japan Series odds for first to 4 in 7", () => {
    const p = 0.39;
    const q = 1 - p;
    const expected =
      p ** 4 * (1 + 4 * q + 10 * q ** 2 + 20 * q ** 3);
    expect(
      seriesWinProb({
        gameProb: p,
        highWins: 0,
        lowWins: 0,
        remaining: 7,
        target: 4,
      })
    ).toBeCloseTo(expected);
  });
});

describe("eloWinProb", () => {
  it("is 0.5 for equal ratings", () => {
    expect(eloWinProb(1500, 1500)).toBeCloseTo(0.5);
  });
});

describe("formatSeriesProb", () => {
  it("formats a series probability label", () => {
    expect(formatSeriesProb("突破率", 0.648)).toBe("突破率64.8%");
    expect(formatSeriesProb("優勝率", 0.2708)).toBe("優勝率27.1%");
    expect(formatSeriesProb("優勝率", null)).toBe("");
  });
});

describe("finalStageFormat", () => {
  it("uses a 2-win advantage when the regular-season gap is 10 games", () => {
    expect(
      finalStageFormat("ソ", "日", {
        ソ: { wins: 91, losses: 49 },
        日: { wins: 78, losses: 62 },
      })
    ).toMatchObject({ advantage: 2, target: 5, maxGames: 7 });
  });

  it("keeps the standard 1-win advantage under 10 games and .500", () => {
    expect(
      finalStageFormat("神", "デ", {
        神: { wins: 79, losses: 62 },
        デ: { wins: 71, losses: 69 },
      })
    ).toMatchObject({ advantage: 1, target: 4, maxGames: 6 });
  });
});

function finished(ateam, bteam, ascore, bscore, stage, league) {
  return {
    series: "クライマックスシリーズ",
    stage,
    league,
    ateam,
    bteam,
    ascore,
    bscore,
    status: "試合終了",
  };
}
