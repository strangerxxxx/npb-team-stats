import { useEffect, useState } from "react";
import TeamLabel from "./TeamLabel";
import { dataUrl } from "../utils/loadCsv";
import {
  formatGameDate,
  formatRatingDelta,
  statusText,
} from "../utils/todayGames";

function Delta({ value }) {
  const text = formatRatingDelta(value);
  if (!text) return null;
  const n = Number(value);
  const cls = n > 0 ? "rating-up" : n < 0 ? "rating-down" : "rating-flat";
  return <span className={`rating-delta ${cls}`}>{text}</span>;
}

function Score({ value, winner }) {
  return (
    <span className={winner ? "today-score today-score-win" : "today-score"}>
      {value}
    </span>
  );
}

const TodayGames = () => {
  const [payload, setPayload] = useState(null);

  useEffect(() => {
    fetch(dataUrl("today_games.json"))
      .then((response) => (response.ok ? response.json() : null))
      .then(setPayload)
      .catch(() => setPayload(null));
  }, []);

  const games = payload?.games || [];
  if (games.length === 0) {
    return null;
  }

  return (
    <section className="panel">
      <h2>当日の試合</h2>
      <p className="panel-lead">
        {payload.date ? `${formatGameDate(payload.date)}のカードです。` : ""}
        終了した試合は結果とレーティング増減を表示します。
      </p>
      <div className="today-grid">
        {games.map((game) => {
          const finished = game.status === "試合終了";
          const showScore =
            (finished || game.status === "試合中") &&
            game.ascore != null &&
            game.bscore != null;
          const aWins =
            finished && Number(game.ascore) > Number(game.bscore);
          const bWins =
            finished && Number(game.bscore) > Number(game.ascore);
          return (
            <div key={`${game.date}-${game.ateam}-${game.bteam}`} className="today-card">
              <div className="today-card-meta">
                <span className={`today-status${game.status === "試合中止" ? " today-status-cancel" : ""}`}>
                  {statusText(game)}
                </span>
                {game.venue ? <span className="today-venue">{game.venue}</span> : null}
              </div>
              <div className="today-matchup">
                <div className="today-side">
                  <TeamLabel abbr={game.ateam} />
                  {finished ? <Delta value={game.a_delta} /> : null}
                </div>
                <div className="today-scoreboard">
                  {showScore ? (
                    <>
                      <Score value={game.ascore} winner={aWins} />
                      <span className="today-score-sep">-</span>
                      <Score value={game.bscore} winner={bWins} />
                    </>
                  ) : (
                    <span className="today-vs">vs</span>
                  )}
                </div>
                <div className="today-side today-side-right">
                  <TeamLabel abbr={game.bteam} />
                  {finished ? <Delta value={game.b_delta} /> : null}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default TodayGames;
