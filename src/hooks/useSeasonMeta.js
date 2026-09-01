import { useEffect, useState } from "react";
import { dataUrl, loadCsv } from "../utils/loadCsv";

export function useSeasonMeta() {
  const [meta, setMeta] = useState(null);

  useEffect(() => {
    const calendarYear = new Date().getFullYear();

    fetch(dataUrl("meta.json"))
      .then((response) => (response.ok ? response.json() : null))
      .catch(() => null)
      .then((json) => {
        if (json?.year) {
          setMeta({
            year: json.year,
            isPreviousSeason: Boolean(
              json.isPreviousSeason ?? json.year < calendarYear
            ),
          });
          return;
        }
        return loadCsv("rating.csv", { header: true }).then((ratings) => {
          const fromCsv = ratings[0]?.date?.slice(0, 4);
          const year = fromCsv ? Number(fromCsv) : null;
          setMeta({
            year,
            isPreviousSeason: year != null && year < calendarYear,
          });
        });
      })
      .catch((err) => console.error(err));
  }, []);

  return meta;
}
