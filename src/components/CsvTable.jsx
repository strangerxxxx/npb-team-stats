import React, { useEffect, useState } from "react";
import { Table } from "react-bootstrap";
import { loadCsv } from "../utils/loadCsv";
import TeamLabel from "./TeamLabel";
import { TEAM_NAMES, isTeamAbbr } from "../constants";
import { heatmapColumnRange, heatmapStyle } from "../utils/heatmap";
import { reorderTable } from "../utils/reorderTable";
import { standingsRowClass } from "../utils/standings";

function parseNumber(value) {
  if (value === "" || value == null) return null;
  const n = Number(String(value).replace("%", ""));
  return Number.isFinite(n) ? n : null;
}

function insertRatingColumn(headers, body, latestRatings) {
  const existing = headers.indexOf("レーティング");
  const nextHeaders = [...headers];
  const nextBody = body.map((row) => [...row]);
  if (existing >= 0) {
    nextHeaders.splice(existing, 1);
    nextBody.forEach((row) => row.splice(existing, 1));
  }
  return {
    headers: [nextHeaders[0], "レーティング", ...nextHeaders.slice(1)],
    body: nextBody.map((row) => {
      const raw = latestRatings[row[0]];
      const rating =
        raw === undefined || raw === "" || !Number.isFinite(Number(raw))
          ? ""
          : Number(raw).toFixed(2);
      return [row[0], rating, ...row.slice(1)];
    }),
  };
}

const CsvTable = ({
  file,
  heatmap = false,
  teamOrder,
  showRating = false,
  leagueSize = 6,
  rankColors = true,
}) => {
  const [data, setData] = useState([]);
  const [error, setError] = useState(null);
  const orderKey = teamOrder ? teamOrder.join(",") : "";

  useEffect(() => {
    Promise.all([
      loadCsv(file, { header: false }),
      showRating ? loadCsv("rating.csv", { header: true }) : Promise.resolve(null),
    ])
      .then(([rows, ratingRows]) => {
        if (rows.length < 2) {
          setData(rows);
          return;
        }
        let [headers, ...body] = rows;
        if (ratingRows?.length) {
          const latest = ratingRows[ratingRows.length - 1];
          ({ headers, body } = insertRatingColumn(headers, body, latest));
        }
        setData(
          reorderTable(
            headers,
            body,
            orderKey ? orderKey.split(",") : undefined
          )
        );
      })
      .catch((err) => {
        console.error(err);
        setError(err.message);
      });
  }, [file, orderKey, showRating]);

  if (error) {
    return <p className="text-danger">{error}</p>;
  }
  if (data.length === 0) {
    return <p className="text-muted">読み込み中...</p>;
  }

  const headers = data[0];
  const body = data.slice(1);
  const matchupHeatmap =
    heatmap && headers.some((header, index) => index > 0 && isTeamAbbr(header));
  const numericCols = heatmap
    ? headers.map((header, col) =>
        heatmapColumnRange(header, col, matchupHeatmap)
      )
    : [];

  return (
    <div className="table-responsive">
      <Table bordered hover size="sm" className="stats-table">
        <thead>
          <tr>
            {headers.map((header, index) => (
              <th key={index}>
                {isTeamAbbr(header) ? TEAM_NAMES[header] : header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.map((row, rowIndex) => (
            <tr
              key={rowIndex}
              className={
                rankColors
                  ? standingsRowClass(rowIndex % leagueSize)
                  : undefined
              }
            >
              {row.map((cell, cellIndex) => {
                const isSelf =
                  cellIndex > 0 &&
                  isTeamAbbr(headers[cellIndex]) &&
                  headers[cellIndex] === row[0];
                const numeric = parseNumber(cell);
                const range = numericCols[cellIndex];
                const useHeatmap =
                  heatmap &&
                  !isSelf &&
                  cellIndex > 0 &&
                  headers[cellIndex] !== "レーティング" &&
                  numeric != null &&
                  range;
                return (
                  <td
                    key={cellIndex}
                    className={isSelf ? "remain-self" : undefined}
                    style={
                      useHeatmap
                        ? heatmapStyle(numeric, range.min, range.max)
                        : undefined
                    }
                  >
                    {cellIndex === 0 && isTeamAbbr(cell) ? (
                      <TeamLabel abbr={cell} />
                    ) : isSelf ? (
                      "―"
                    ) : (
                      cell
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </Table>
    </div>
  );
};

export default CsvTable;
