import TeamLabel from "./TeamLabel";
import { formatSeriesProb } from "../utils/postseason";

function TeamRow({ row, decided, probLabel }) {
  const classes = [
    "bracket-team",
    row.isWinner ? "is-winner" : "",
    decided && row.abbr && !row.isWinner ? "is-loser" : "",
  ]
    .filter(Boolean)
    .join(" ");
  const probText = formatSeriesProb(probLabel, row.prob);
  return (
    <div className={classes}>
      <span className="bracket-seed">{row.seed || ""}</span>
      <div className="bracket-team-info">
        {row.abbr ? (
          <TeamLabel abbr={row.abbr} />
        ) : (
          <span className="bracket-tbd">未定</span>
        )}
        {probText ? <span className="bracket-prob">{probText}</span> : null}
      </div>
      <span className="bracket-wins">
        {row.advantage ? <span className="bracket-adv">ADV</span> : null}
        {row.abbr ? row.wins : "–"}
      </span>
    </div>
  );
}

function Match({ match }) {
  if (!match) return null;
  return (
    <div className="bracket-match">
      <p className="bracket-round">{match.title}</p>
      {match.rows.map((row, index) => (
        <TeamRow
          key={row.abbr || `empty-${index}`}
          row={row}
          decided={Boolean(match.winner)}
          probLabel={match.winner ? "" : match.probLabel}
        />
      ))}
      {match.note ? <p className="bracket-note">{match.note}</p> : null}
    </div>
  );
}

const PostseasonBracket = ({ bracket }) => {
  if (!bracket) return null;
  return (
    <section className="panel">
      <h2>クライマックスシリーズ・日本シリーズ</h2>
      <div className="bracket">
        {bracket.leagues.map((league) => (
          <div key={league.id} className={`bracket-league bracket-${league.id}`}>
            <h3>{league.name}</h3>
            <Match match={league.first} />
            <div className="bracket-connector" aria-hidden="true" />
            <Match match={league.final} />
          </div>
        ))}
        <div className="bracket-japan">
          <Match match={bracket.japan} />
        </div>
      </div>
    </section>
  );
};

export default PostseasonBracket;
