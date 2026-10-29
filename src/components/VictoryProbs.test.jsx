import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import VictoryProbs from "./VictoryProbs";

const history = {
  count: 100000,
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

describe("VictoryProbs", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        json: async () => history,
      }))
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("defaults to the latest date and can rewind to an earlier snapshot", async () => {
    render(<VictoryProbs />);
    expect(
      await screen.findByText("4月3日終了時点の残り試合を10万回シミュレーションした最終順位の割合です。")
    ).toBeInTheDocument();
    expect(screen.getByText("80.00")).toBeInTheDocument();
    const dateInput = screen.getByLabelText("表示する日付");
    expect(dateInput).toHaveAttribute("min", "2026-04-01");
    expect(dateInput).toHaveAttribute("max", "2026-04-03");
    fireEvent.change(screen.getByLabelText("表示日"), { target: { value: "0" } });
    expect(screen.getByText("4月1日終了時点の残り試合を10万回シミュレーションした最終順位の割合です。")).toBeInTheDocument();
    expect(screen.getAllByText("40.00").length).toBeGreaterThan(0);
    expect(screen.queryByText("80.00")).not.toBeInTheDocument();
    fireEvent.change(dateInput, { target: { value: "2026-04-02" } });
    expect(screen.getByText("4月2日終了時点の残り試合を10万回シミュレーションした最終順位の割合です。")).toBeInTheDocument();
    expect(screen.getAllByText("40.00").length).toBeGreaterThan(0);
  });
});
