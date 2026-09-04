import { afterEach, describe, expect, it, vi } from "vitest";
import { dataUrl } from "./loadCsv";

describe("dataUrl", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("uses the app base path when no remote data URL is set", () => {
    vi.stubEnv("VITE_DATA_BASE_URL", "");
    expect(dataUrl("meta.json")).toBe("/data/meta.json");
  });

  it("uses VITE_DATA_BASE_URL when set", () => {
    vi.stubEnv(
      "VITE_DATA_BASE_URL",
      "https://example.s3.ap-northeast-1.amazonaws.com/data/"
    );
    expect(dataUrl("today_games.json")).toBe(
      "https://example.s3.ap-northeast-1.amazonaws.com/data/today_games.json"
    );
  });
});
