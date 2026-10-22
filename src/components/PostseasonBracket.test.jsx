import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import PostseasonBracket from "./PostseasonBracket";
import { buildBracket } from "../utils/postseason";

describe("PostseasonBracket", () => {
  it("renders league CS rounds and Japan Series", () => {
    const bracket = buildBracket(
      [
        {
          series: "クライマックスシリーズ",
          stage: "ファーストステージ",
          league: "central",
          ateam: "巨",
          bteam: "デ",
          ascore: "1",
          bscore: "2",
          status: "試合終了",
        },
        {
          series: "クライマックスシリーズ",
          stage: "ファーストステージ",
          league: "central",
          ateam: "巨",
          bteam: "デ",
          ascore: "1",
          bscore: "4",
          status: "試合終了",
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
      ],
      { 神: 1, 巨: 2, デ: 3, ソ: 1, 西: 2, 日: 3 }
    );
    render(<PostseasonBracket bracket={bracket} />);
    expect(screen.getByText("クライマックスシリーズ・日本シリーズ")).toBeInTheDocument();
    expect(screen.getByText("セ・リーグ")).toBeInTheDocument();
    expect(screen.getByText("パ・リーグ")).toBeInTheDocument();
    expect(screen.getAllByText("ファーストステージ")).toHaveLength(2);
    expect(screen.getAllByText("ファイナルステージ")).toHaveLength(2);
    expect(screen.getByText("日本シリーズ")).toBeInTheDocument();
    expect(screen.getAllByText("ADV").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/優勝率/).length).toBe(2);
    expect(screen.queryByText(/突破率/)).toBeNull();
  });

  it("shows 突破率 on an undecided Climax Series match", () => {
    const bracket = buildBracket(
      [
        {
          series: "クライマックスシリーズ",
          stage: "ファーストステージ",
          league: "central",
          ateam: "巨",
          bteam: "デ",
          ascore: "1",
          bscore: "2",
          status: "試合終了",
          a_rating: 1540,
          b_rating: 1500,
        },
        {
          series: "クライマックスシリーズ",
          stage: "ファーストステージ",
          league: "central",
          ateam: "巨",
          bteam: "デ",
          status: "試合前",
          a_rating: 1540,
          b_rating: 1500,
        },
      ],
      { 神: 1, 巨: 2, デ: 3, ソ: 1, 西: 2, 日: 3 }
    );
    render(<PostseasonBracket bracket={bracket} />);
    expect(screen.getAllByText(/突破率/).length).toBe(2);
    expect(screen.queryByText(/優勝率/)).toBeNull();
  });
});
