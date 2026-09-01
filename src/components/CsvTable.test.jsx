import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import CsvTable from "./CsvTable";
import { heatmapStyle } from "../utils/heatmap";
import { loadCsv } from "../utils/loadCsv";

vi.mock("../utils/loadCsv", () => ({
  loadCsv: vi.fn(),
}));

const VICTORY = [
  ["チーム名", "1位", "2位", "3位", "4位", "5位", "6位"],
  ["神", "97.35", "2.65", "0.00", "0.00", "0.00", "0.00"],
  ["巨", "2.65", "96.17", "20.00", "0.00", "0.00", "0.00"],
];

const MATCHUP = [
  ["チーム名", "神", "ソ"],
  ["ヤ", "20.00", "24.51"],
  ["ソ", "80.00", "75.49"],
];

describe("CsvTable", () => {
  beforeEach(() => {
    loadCsv.mockImplementation(async (file) => {
      if (file === "victory.csv") return VICTORY;
      if (file === "win_prob.csv") return MATCHUP;
      return [];
    });
  });

  it("does not paint the 1st-place row gold when rankColors is false", async () => {
    const { container } = render(
      <CsvTable file="victory.csv" heatmap rankColors={false} />
    );
    await screen.findByText("97.35");
    expect(container.querySelector(".standings-leader")).toBeNull();
  });

  it("paints 0% rank probability as white on a 0–100 scale", async () => {
    render(<CsvTable file="victory.csv" heatmap rankColors={false} />);
    const zeros = await screen.findAllByText("0.00");
    expect(zeros[0]).toHaveStyle({
      backgroundColor: heatmapStyle(0, 0, 100).backgroundColor,
    });
    const twenty = screen.getAllByText("20.00")[0];
    expect(twenty).toHaveStyle({
      backgroundColor: heatmapStyle(20, 0, 100).backgroundColor,
    });
    expect(heatmapStyle(20, 0, 100).backgroundColor).not.toBe(
      heatmapStyle(20, 20, 80).backgroundColor
    );
  });

  it("paints matchup win probability on a 20–80 scale", async () => {
    render(<CsvTable file="win_prob.csv" heatmap rankColors={false} />);
    const twenty = await screen.findByText("20.00");
    expect(twenty).toHaveStyle({
      backgroundColor: heatmapStyle(20, 20, 80).backgroundColor,
    });
    expect(screen.getByText("80.00")).toHaveStyle({
      backgroundColor: heatmapStyle(80, 20, 80).backgroundColor,
    });
    expect(screen.getByText("24.51")).toHaveStyle({
      backgroundColor: heatmapStyle(24.51, 20, 80).backgroundColor,
    });
  });
});
