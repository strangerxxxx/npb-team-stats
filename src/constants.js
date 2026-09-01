export const TEAM_COLORS = {
  神: "#FFE100",
  広: "#E50012",
  デ: "#0093C9",
  巨: "#FF7820",
  ヤ: "#96c800",
  中: "#003595",
  オ: "#AA9010",
  ロ: "#CCCCCC",
  ソ: "#FBC700",
  楽: "#870010",
  西: "#00215B",
  日: "#01609A",
};

export const TEAM_NAMES = {
  神: "阪神",
  広: "広島",
  デ: "DeNA",
  巨: "巨人",
  ヤ: "ヤクルト",
  中: "中日",
  オ: "オリックス",
  ロ: "ロッテ",
  ソ: "ソフトバンク",
  楽: "楽天",
  西: "西武",
  日: "日本ハム",
};

export const CENTRAL = ["神", "広", "デ", "巨", "ヤ", "中"];
export const PACIFIC = ["オ", "ロ", "ソ", "楽", "西", "日"];

export function isTeamAbbr(value) {
  return Object.hasOwn(TEAM_NAMES, value);
}
