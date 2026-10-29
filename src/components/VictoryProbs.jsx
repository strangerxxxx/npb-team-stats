import { useEffect, useMemo, useState } from "react";
import { Button, Col, Row } from "react-bootstrap";
import CsvTable from "./CsvTable";
import { dataUrl } from "../utils/loadCsv";
import { formatGameDate } from "../utils/todayGames";
import {
  addDays,
  clampDate,
  dayOffset,
  formatSimCount,
  indexForDate,
  isDecidedProbs,
  isHistoryPayload,
  leagueSnapshot,
} from "../utils/victoryProbs";

function FallbackTables({ centralOrder, pacificOrder }) {
  return (
    <Row>
      <Col md={6}>
        <h3>セ・リーグ</h3>
        <CsvTable
          file="victory_prob_central.csv"
          heatmap
          teamOrder={centralOrder}
          rankColors={false}
        />
      </Col>
      <Col md={6}>
        <h3>パ・リーグ</h3>
        <CsvTable
          file="victory_prob_pacific.csv"
          heatmap
          teamOrder={pacificOrder}
          rankColors={false}
        />
      </Col>
    </Row>
  );
}

const VictoryProbs = ({ centralOrder, pacificOrder }) => {
  const [payload, setPayload] = useState(null);
  const [selectedDate, setSelectedDate] = useState("");
  const [mode, setMode] = useState("loading");

  useEffect(() => {
    fetch(dataUrl("victory_prob_history.json"))
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (!isHistoryPayload(data)) {
          setMode("csv");
          return;
        }
        setPayload(data);
        setSelectedDate(data.dates[data.dates.length - 1]);
        setMode("history");
      })
      .catch(() => setMode("csv"));
  }, []);

  const dates = payload?.dates || [];
  const minDate = dates[0] || "";
  const maxDate = dates[dates.length - 1] || "";
  const date = selectedDate || maxDate;
  const index = indexForDate(dates, date);
  const span = minDate && maxDate ? dayOffset(minDate, maxDate) : 0;
  const count = payload?.count || 100000;
  const decided = isDecidedProbs(payload?.probs?.[index]);
  const centralRows = useMemo(
    () => (payload ? leagueSnapshot(payload, index, 0) : []),
    [payload, index]
  );
  const pacificRows = useMemo(
    () => (payload ? leagueSnapshot(payload, index, 6) : []),
    [payload, index]
  );

  return (
    <section className="panel">
      <h2>最終順位確率（％）</h2>
      {mode === "history" && date ? (
        <>
          <p className="panel-lead">
            {decided
              ? `${formatGameDate(date)}終了時点のレギュラーシーズン最終順位です。`
              : `${formatGameDate(date)}終了時点の残り試合を${formatSimCount(count)}回シミュレーションした最終順位の割合です。`}
          </p>
          <div className="victory-date-controls">
            <label className="victory-date-label" htmlFor="victory-date-slider">
              表示日
            </label>
            <input
              id="victory-date-slider"
              className="victory-date-slider"
              type="range"
              min={0}
              max={span}
              step={1}
              value={dayOffset(minDate, date)}
              aria-valuetext={date}
              onChange={(event) =>
                setSelectedDate(addDays(minDate, Number(event.target.value)))
              }
            />
            <input
              className="victory-date-input"
              type="date"
              min={minDate}
              max={maxDate}
              value={date}
              aria-label="表示する日付"
              onChange={(event) =>
                setSelectedDate(clampDate(event.target.value, minDate, maxDate))
              }
            />
            <Button
              type="button"
              variant={date === maxDate ? "success" : "outline-success"}
              size="sm"
              disabled={date === maxDate}
              onClick={() => setSelectedDate(maxDate)}
            >
              最新
            </Button>
          </div>
          <Row>
            <Col md={6}>
              <h3>セ・リーグ</h3>
              <CsvTable
                rows={centralRows}
                heatmap
                teamOrder={centralOrder}
                rankColors={false}
              />
            </Col>
            <Col md={6}>
              <h3>パ・リーグ</h3>
              <CsvTable
                rows={pacificRows}
                heatmap
                teamOrder={pacificOrder}
                rankColors={false}
              />
            </Col>
          </Row>
        </>
      ) : mode === "csv" ? (
        <>
          <p className="panel-lead">
            残り試合を10万回シミュレーションした最終順位の割合です。
          </p>
          <FallbackTables
            centralOrder={centralOrder}
            pacificOrder={pacificOrder}
          />
        </>
      ) : (
        <p className="panel-lead">読み込み中...</p>
      )}
    </section>
  );
};

export default VictoryProbs;
