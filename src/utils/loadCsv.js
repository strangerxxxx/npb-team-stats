import Papa from "papaparse";

export function dataUrl(filename) {
  const remote = import.meta.env.VITE_DATA_BASE_URL;
  if (remote) {
    return `${String(remote).replace(/\/+$/, "")}/${filename}`;
  }
  return `${import.meta.env.BASE_URL}data/${filename}`;
}

export async function loadCsv(filename, { header = true } = {}) {
  const response = await fetch(dataUrl(filename));
  if (!response.ok) {
    throw new Error(`${filename} の読み込みに失敗しました (${response.status})`);
  }
  const parsed = Papa.parse(await response.text(), {
    header,
    skipEmptyLines: true,
  });
  return parsed.data.filter((row) =>
    (Array.isArray(row) ? row : Object.values(row)).some(
      (value) => String(value).trim() !== ""
    )
  );
}
