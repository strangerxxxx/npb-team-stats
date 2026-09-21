import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import TodayGames from "./TodayGames";

const payload = {
  date: "2026-09-01",
  games: [
    {
      date: "2026-09-01",
      ateam: "巨",
      bteam: "デ",
      ascore: "4",
      bscore: "3",
      status: "試合終了",
      venue: "京セラD大阪",
      note: "",
      a_delta: 8.12,
      b_delta: -8.12,
      a_rating: 1508.0,
      b_rating: 1492.0,
      a_win_pct: 0.523,
      b_win_pct: 0.477,
    },
    {
      date: "2026-09-01",
      ateam: "ヤ",
      bteam: "神",
      ascore: "2",
      bscore: "1",
      status: "試合中",
      venue: "神宮",
      note: "5回表",
      a_delta: null,
      b_delta: null,
      a_rating: 1500.0,
      b_rating: 1500.0,
      a_win_pct: 0.5,
      b_win_pct: 0.5,
    },
    {
      date: "2026-09-01",
      ateam: "中",
      bteam: "広",
      ascore: "0",
      bscore: "0",
      status: "試合中止",
      venue: "バンテリン",
      note: "",
      a_delta: null,
      b_delta: null,
      a_rating: 1458.57,
      b_rating: 1451.76,
      a_win_pct: 0.51,
      b_win_pct: 0.49,
    },
    {
      date: "2026-09-01",
      ateam: "日",
      bteam: "ソ",
      ascore: null,
      bscore: null,
      status: "試合前",
      venue: "エスコンＦ",
      note: "18:00",
      a_delta: null,
      b_delta: null,
      a_rating: 1574.96,
      b_rating: 1591.33,
      a_win_pct: 0.476,
      b_win_pct: 0.524,
    },
  ],
  yesterday: {
    date: "2026-08-31",
    games: [
      {
        date: "2026-08-31",
        ateam: "西",
        bteam: "楽",
        ascore: "5",
        bscore: "2",
        status: "試合終了",
        venue: "",
        note: "",
        a_delta: 7.21,
        b_delta: -7.21,
        a_rating: 1560.0,
        b_rating: 1465.0,
        a_win_pct: 0.6337,
        b_win_pct: 0.3663,
      },
    ],
  },
};

describe("TodayGames", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        json: async () => payload,
      }))
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows today's results with rating, win pct, and yesterday's games", async () => {
    render(<TodayGames />);
    expect(await screen.findByText("本日の試合")).toBeInTheDocument();
    expect(screen.getByText("昨日の試合")).toBeInTheDocument();
    expect(screen.getByText("巨人")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("+8.12")).toBeInTheDocument();
    expect(screen.getByText("-8.12")).toBeInTheDocument();
    expect(screen.getByText("1508.00")).toBeInTheDocument();
    expect(screen.getByText("勝率52.3%")).toBeInTheDocument();
    expect(screen.getByText("勝率47.7%")).toBeInTheDocument();
    expect(screen.getByText("勝率63.4%")).toBeInTheDocument();
    expect(screen.getByText("勝率36.6%")).toBeInTheDocument();
    expect(screen.getByText("5回表")).toBeInTheDocument();
    expect(screen.getByText("試合中止")).toBeInTheDocument();
    expect(screen.getByText("18:00")).toBeInTheDocument();
    expect(screen.getAllByText("vs")).toHaveLength(2);
    expect(screen.getByText("西武")).toBeInTheDocument();
    expect(screen.getByText("楽天")).toBeInTheDocument();
    expect(screen.getByText("8月31日の結果です。")).toBeInTheDocument();
  });
});
