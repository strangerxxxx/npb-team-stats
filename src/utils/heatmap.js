import { isTeamAbbr } from "../constants";

export const HEAT_RGB = [22, 99, 72];

export function heatmapStyle(value, min, max) {
  if (value == null || max <= min) return undefined;
  const t = Math.max(0, Math.min(1, (value - min) / (max - min)));
  const [hr, hg, hb] = HEAT_RGB;
  const r = Math.round(255 + (hr - 255) * t);
  const g = Math.round(255 + (hg - 255) * t);
  const b = Math.round(255 + (hb - 255) * t);
  return { backgroundColor: `rgb(${r}, ${g}, ${b})` };
}

export function heatmapColumnRange(header, col, matchupHeatmap) {
  if (col === 0 || header === "レーティング") return null;
  if (matchupHeatmap) {
    return isTeamAbbr(header) ? { min: 20, max: 80 } : null;
  }
  return { min: 0, max: 100 };
}
