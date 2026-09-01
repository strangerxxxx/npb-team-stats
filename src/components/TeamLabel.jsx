import { TEAM_COLORS, TEAM_NAMES } from "../constants";

const TeamLabel = ({ abbr, showAbbr = false }) => (
  <span className="team-label">
    <span
      className="team-swatch"
      style={{ backgroundColor: TEAM_COLORS[abbr] ?? "#888" }}
    />
    <span className="team-name">{TEAM_NAMES[abbr] ?? abbr}</span>
    {showAbbr && abbr !== TEAM_NAMES[abbr] && (
      <span className="team-abbr">{abbr}</span>
    )}
  </span>
);

export default TeamLabel;
