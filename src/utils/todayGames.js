export function formatRatingDelta(value) {
  if (value == null || value === "" || !Number.isFinite(Number(value))) {
    return "";
  }
  const n = Number(value);
  if (n > 0) return `+${n.toFixed(2)}`;
  if (n < 0) return n.toFixed(2);
  return "0.00";
}

export function formatGameDate(iso) {
  if (!iso) return "";
  const match = String(iso).match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return iso;
  return `${Number(match[2])}月${Number(match[3])}日`;
}

export function statusText(game) {
  if (game.status === "試合前" && game.note) return game.note;
  if (game.status === "試合中" && game.note) return game.note;
  return game.status || "";
}
