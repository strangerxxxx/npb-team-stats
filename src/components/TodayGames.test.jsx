import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import TodayGames from "./TodayGames";

describe("TodayGames", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        json: async () => ({
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
            },
          ],
        }),
      }))
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows finished results with rating deltas and scheduled start time", async () => {
    render(<TodayGames />);
    expect(await screen.findByText("当日の試合")).toBeInTheDocument();
    expect(screen.getByText("巨人")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("+8.12")).toBeInTheDocument();
    expect(screen.getByText("-8.12")).toBeInTheDocument();
    expect(screen.getByText("5回表")).toBeInTheDocument();
    expect(screen.getByText("試合中止")).toBeInTheDocument();
    expect(screen.getByText("18:00")).toBeInTheDocument();
    expect(screen.getAllByText("vs")).toHaveLength(2);
  });
});
