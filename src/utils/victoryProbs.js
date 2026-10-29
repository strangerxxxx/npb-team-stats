export function formatSimCount(count) {
  if (count === 100000) return "10万";
  return Number(count).toLocaleString("ja-JP");
}

export const RANK_HEADERS = ["チーム名", "1位", "2位", "3位", "4位", "5位", "6位"];

export function snapshotRows(probs, names) {
  if (!probs?.length || !names?.length) return [];
  return [
    RANK_HEADERS,
    ...names.map((name, index) => [
      name,
      ...(probs[index] || []).map((value) => Number(value).toFixed(2)),
    ]),
  ];
}

export function leagueSnapshot(payload, dateIndex, start) {
  const teams = payload?.teams || [];
  const probs = payload?.probs?.[dateIndex] || [];
  return snapshotRows(probs.slice(start, start + 6), teams.slice(start, start + 6));
}

export function addDays(iso, days) {
  const [year, month, day] = String(iso).split("-").map(Number);
  if (!year || !month || !day) return "";
  const date = new Date(Date.UTC(year, month - 1, day + Number(days)));
  return date.toISOString().slice(0, 10);
}

export function dayOffset(start, iso) {
  const from = Date.parse(`${start}T00:00:00Z`);
  const to = Date.parse(`${iso}T00:00:00Z`);
  if (!Number.isFinite(from) || !Number.isFinite(to)) return 0;
  return Math.round((to - from) / 86400000);
}

export function clampDate(iso, min, max) {
  if (!iso) return min || "";
  if (min && iso < min) return min;
  if (max && iso > max) return max;
  return iso;
}

export function indexForDate(dates, iso) {
  if (!dates?.length) return 0;
  let index = 0;
  for (let i = 0; i < dates.length; i += 1) {
    if (dates[i] <= iso) index = i;
    else break;
  }
  return index;
}

export function isHistoryPayload(data) {
  return Boolean(
    data?.dates?.length &&
      data?.probs?.length === data.dates.length &&
      data?.teams?.length
  );
}

export function isDecidedProbs(probs) {
  if (!probs?.length) return false;
  const leagues = [probs.slice(0, 6), probs.slice(6, 12)];
  return leagues.every(
    (rows) =>
      rows.length === 6 &&
      rows.every((row) => {
        const values = (row || []).map(Number);
        const hundreds = values.filter((value) => value >= 99.99).length;
        const total = values.reduce((sum, value) => sum + value, 0);
        return hundreds === 1 && Math.abs(total - 100) < 0.05;
      })
  );
}
