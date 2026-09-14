import { useEffect, useState } from "react";
import TeamLabel from "./TeamLabel";
import { dataUrl } from "../utils/loadCsv";
import {
  formatGameDate,
  formatRating,
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

function SideStats({ rating, winPct, delta, finished }) {
  const ratingText = formatRating(rating);
  return (
    <div className="today-side-stats">
      {ratingText ? <span className="today-rating">{ratingText}</span> : null}
      {winPct ? <span className="today-winpct">{winPct}</span> : null}
      {finished ? <Delta value={delta} /> : null}
    </div>
  );
}

export function GameCard({ game }) {
  const finished = game.status === "試合終了";
  const showScore =
    (finished || game.status === "試合中") &&
    game.ascore != null &&
    game.bscore != null;
  const aWins = finished && Number(game.ascore) > Number(game.bscore);
  const bWins = finished && Number(game.bscore) > Number(game.ascore);
  return (
    <div className="today-card">
      <div className="today-card-meta">
        <span
          className={`today-status${game.status === "試合中止" ? " today-status-cancel" : ""}`}
        >
          {statusText(game)}
        </span>
        {game.venue ? <span className="today-venue">{game.venue}</span> : null}
      </div>
      <div className="today-matchup">
        <div className="today-side">
          <TeamLabel abbr={game.ateam} />
          <SideStats
            rating={game.a_rating}
            winPct={game.a_win_pct}
            delta={game.a_delta}
            finished={finished}
          />
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
          <SideStats
            rating={game.b_rating}
            winPct={game.b_win_pct}
            delta={game.b_delta}
            finished={finished}
          />
        </div>
      </div>
    </div>
  );
}

function GamesBlock({ title, date, games, lead }) {
  if (!games.length) return null;
  return (
    <section className="panel">
      <h2>{title}</h2>
      <p className="panel-lead">
        {date ? `${formatGameDate(date)}${lead}` : lead.replace(/^の/, "")}
      </p>
      <div className="today-grid">
        {games.map((game, index) => (
          <GameCard
            key={`${game.date}-${game.ateam}-${game.bteam}-${index}`}
            game={game}
          />
        ))}
      </div>
    </section>
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
  const yesterday = payload?.yesterday || {};
  const yesterdayGames = yesterday.games || [];
  if (games.length === 0 && yesterdayGames.length === 0) {
    return null;
  }

  return (
    <>
      <GamesBlock
        title="本日の試合"
        date={payload.date}
        games={games}
        lead="のカードです。終了した試合は結果とレーティング増減を表示します。"
      />
      <GamesBlock
        title="昨日の試合"
        date={yesterday.date}
        games={yesterdayGames}
        lead="の結果です。"
      />
    </>
  );
};

export default TodayGames;
