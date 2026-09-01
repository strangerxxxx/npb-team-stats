import React from "react";
import { Table } from "react-bootstrap";
import TeamLabel from "./TeamLabel";
import {
  formatGamesBehind,
  formatWinPct,
  standingsRowClass,
} from "../utils/standings";

const LeagueStandings = ({ title, teams }) => (
  <div>
    <h3>{title}</h3>
    <div className="table-responsive">
      <Table bordered hover size="sm" className="stats-table has-rank-col mb-3">
        <thead>
          <tr>
            <th>順</th>
            <th>チーム</th>
            <th>試</th>
            <th>勝</th>
            <th>敗</th>
            <th>分</th>
            <th>勝率</th>
            <th>差</th>
            <th>残</th>
          </tr>
        </thead>
        <tbody>
          {teams.map((team, index) => (
            <tr key={team.abbr} className={standingsRowClass(index, team)}>
              <td>{team.rank}</td>
              <td>
                <TeamLabel abbr={team.abbr} />
              </td>
              <td>{team.games}</td>
              <td>{team.wins}</td>
              <td>{team.losses}</td>
              <td>{team.draws}</td>
              <td>{formatWinPct(team.wins, team.losses)}</td>
              <td className="gb-cell">
                {team.magic ? (
                  <span className="magic-pennant">{team.magic}</span>
                ) : (
                  formatGamesBehind(team.gb, team.isLeader)
                )}
              </td>
              <td>{team.remaining}</td>
            </tr>
          ))}
        </tbody>
      </Table>
    </div>
  </div>
);

const RemainingMatrix = ({ title, teams }) => (
  <div>
    <h3>{title}</h3>
    <div className="table-responsive">
      <Table bordered hover size="sm" className="stats-table remain-table mb-3">
        <thead>
          <tr>
            <th></th>
            {teams.map((team) => (
              <th key={team.abbr}>{team.abbr}</th>
            ))}
            <th>交</th>
          </tr>
        </thead>
        <tbody>
          {teams.map((team, index) => (
            <tr key={team.abbr} className={standingsRowClass(index, team)}>
              <th>
                <TeamLabel abbr={team.abbr} />
              </th>
              {teams.map((opp) => (
                <td
                  key={opp.abbr}
                  className={team.abbr === opp.abbr ? "remain-self" : undefined}
                >
                  {team.abbr === opp.abbr ? "―" : team.remainVs[opp.abbr]}
                </td>
              ))}
              <td>{team.remainInterleague}</td>
            </tr>
          ))}
        </tbody>
      </Table>
    </div>
  </div>
);

const Standings = ({ leagues, error }) => {
  if (error) {
    return <p className="text-danger">{error}</p>;
  }
  if (!leagues) {
    return <p className="text-muted">読み込み中...</p>;
  }

  return (
    <>
      <div className="league-grid">
        <LeagueStandings title="セ・リーグ" teams={leagues.central} />
        <LeagueStandings title="パ・リーグ" teams={leagues.pacific} />
      </div>
      <h3 className="remain-heading">残り試合</h3>
      <div className="league-grid">
        <RemainingMatrix title="セ・リーグ" teams={leagues.central} />
        <RemainingMatrix title="パ・リーグ" teams={leagues.pacific} />
      </div>
    </>
  );
};

export default Standings;
