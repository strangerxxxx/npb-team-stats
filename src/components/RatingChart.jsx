import React, { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Brush,
} from "recharts";
import { Button } from "react-bootstrap";
import { loadCsv } from "../utils/loadCsv";
import { TEAM_COLORS, TEAM_NAMES } from "../constants";
import { ratingYDomain, seriesVisibility } from "../utils/ratingChart";

const LEAGUE_OPTIONS = [
  { id: "all", label: "全体" },
  { id: "central", label: "セ・リーグ" },
  { id: "pacific", label: "パ・リーグ" },
];

const CHART_HEIGHT = 420;

const RatingChart = ({ teamOrder }) => {
  const [league, setLeague] = useState("all");
  const [data, setData] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCsv("rating.csv", { header: true })
      .then(setData)
      .catch((err) => {
        console.error(err);
        setError(err.message);
      });
  }, []);

  const yDomain = useMemo(() => ratingYDomain(data), [data]);

  const seriesKeys = data.length
    ? teamOrder?.length
      ? teamOrder.filter((key) => key in data[0])
      : Object.keys(data[0]).filter((key) => key !== "date")
    : [];
  const series = seriesVisibility(seriesKeys, league);

  return (
    <div>
      <div className="btn-group mb-3 league-toggle" role="group">
        {LEAGUE_OPTIONS.map(({ id, label }) => (
          <Button
            key={id}
            type="button"
            variant={league === id ? "success" : "outline-success"}
            onClick={() => setLeague(id)}
          >
            {label}
          </Button>
        ))}
      </div>
      {error && <p className="text-danger">{error}</p>}
      <div className="rating-chart" style={{ height: CHART_HEIGHT }}>
        {data.length > 0 && (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data}
              margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8e4" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis
                domain={yDomain}
                tick={{ fontSize: 12 }}
                allowDataOverflow
              />
              <Tooltip
                formatter={(value, key) => [
                  Number(value).toFixed(1),
                  TEAM_NAMES[key] ?? key,
                ]}
              />
              <Legend formatter={(key) => TEAM_NAMES[key] ?? key} />
              {series.map(({ key, hidden }) => (
                <Line
                  type="linear"
                  dataKey={key}
                  name={key}
                  stroke={TEAM_COLORS[key] ?? "#888888"}
                  strokeWidth={2}
                  key={key}
                  dot={false}
                  hide={hidden}
                  legendType={hidden ? "none" : "line"}
                  isAnimationActive
                />
              ))}
              <Brush dataKey="date" stroke="#1f6b4a" height={28} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

export default RatingChart;
