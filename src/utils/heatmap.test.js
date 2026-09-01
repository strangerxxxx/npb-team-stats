import { describe, expect, it } from "vitest";
import { heatmapColumnRange, heatmapStyle, HEAT_RGB } from "./heatmap";

const WHITE = "rgb(255, 255, 255)";
const FULL = `rgb(${HEAT_RGB.join(", ")})`;

describe("heatmapStyle", () => {
  it("maps 0% to white and 100% to the full green", () => {
    expect(heatmapStyle(0, 0, 100)).toEqual({ backgroundColor: WHITE });
    expect(heatmapStyle(100, 0, 100)).toEqual({ backgroundColor: FULL });
  });

  it("clamps the 20–80 matchup scale so 0% and 20% are white", () => {
    expect(heatmapStyle(0, 20, 80)).toEqual({ backgroundColor: WHITE });
    expect(heatmapStyle(20, 20, 80)).toEqual({ backgroundColor: WHITE });
    expect(heatmapStyle(80, 20, 80)).toEqual({ backgroundColor: FULL });
    expect(heatmapStyle(100, 20, 80)).toEqual({ backgroundColor: FULL });
  });

  it("returns no style when the range is invalid", () => {
    expect(heatmapStyle(50, 80, 20)).toBeUndefined();
    expect(heatmapStyle(null, 0, 100)).toBeUndefined();
  });
});

describe("heatmapColumnRange", () => {
  it("uses 20–80 for matchup team columns", () => {
    expect(heatmapColumnRange("チーム名", 0, true)).toBeNull();
    expect(heatmapColumnRange("レーティング", 1, true)).toBeNull();
    expect(heatmapColumnRange("神", 2, true)).toEqual({ min: 20, max: 80 });
    expect(heatmapColumnRange("1位", 1, true)).toBeNull();
  });

  it("uses 0–100 for rank-probability columns", () => {
    expect(heatmapColumnRange("1位", 1, false)).toEqual({ min: 0, max: 100 });
    expect(heatmapColumnRange("チーム名", 0, false)).toBeNull();
  });
});
