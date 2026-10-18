import { useEffect, useMemo, useState } from "react";
import { Button, Col, Row } from "react-bootstrap";
import CsvTable from "./CsvTable";
import { dataUrl } from "../utils/loadCsv";
import { formatGameDate } from "../utils/todayGames";
import {
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
  const [index, setIndex] = useState(0);
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
        setIndex(data.dates.length - 1);
        setMode("history");
      })
      .catch(() => setMode("csv"));
  }, []);

  const lastIndex = (payload?.dates?.length || 1) - 1;
  const date = payload?.dates?.[index];
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
              max={lastIndex}
              step={1}
              value={index}
              aria-valuetext={date}
              onChange={(event) => setIndex(Number(event.target.value))}
            />
            <input
              className="victory-date-input"
              type="date"
              min={payload.dates[0]}
              max={payload.dates[lastIndex]}
              value={date}
              aria-label="表示する日付"
              onChange={(event) =>
                setIndex(indexForDate(payload.dates, event.target.value))
              }
            />
            <Button
              type="button"
              variant={index === lastIndex ? "success" : "outline-success"}
              size="sm"
              disabled={index === lastIndex}
              onClick={() => setIndex(lastIndex)}
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
