import { useEffect, useState } from "react";
import { dataUrl, loadCsv } from "../utils/loadCsv";
import { splitStandings } from "../utils/standings";

export function useStandings() {
  const [leagues, setLeagues] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([
      loadCsv("standings.csv", { header: true }),
      loadCsv("h2h.csv", { header: true }).catch(() => []),
      fetch(dataUrl("meta.json"))
        .then((response) => (response.ok ? response.json() : null))
        .catch(() => null),
    ])
      .then(([rows, h2hRows, meta]) =>
        setLeagues(splitStandings(rows, h2hRows, meta?.prevRanks || {}))
      )
      .catch((err) => {
        console.error(err);
        setError(err.message);
      });
  }, []);

  return { leagues, error };
}

export function teamOrder(teams) {
  return teams.map((team) => team.abbr);
}
