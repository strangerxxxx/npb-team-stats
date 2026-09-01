import "./App.css";
import { lazy, Suspense, useMemo } from "react";
import Standings from "./components/Standings";
import CsvTable from "./components/CsvTable";
import { Container, Row, Col } from "react-bootstrap";
import { teamOrder, useStandings } from "./hooks/useStandings";
import { useSeasonMeta } from "./hooks/useSeasonMeta";

const RatingChart = lazy(() => import("./components/RatingChart"));

const iconUrl = `${import.meta.env.BASE_URL}icon.png`;

function App() {
  const { leagues, error } = useStandings();
  const season = useSeasonMeta();
  const centralOrder = useMemo(
    () => (leagues ? teamOrder(leagues.central) : undefined),
    [leagues]
  );
  const pacificOrder = useMemo(
    () => (leagues ? teamOrder(leagues.pacific) : undefined),
    [leagues]
  );
  const allOrder = useMemo(
    () =>
      centralOrder && pacificOrder
        ? [...centralOrder, ...pacificOrder]
        : undefined,
    [centralOrder, pacificOrder]
  );

  return (
    <div className="page">
      <header className="site-header">
        <Container>
          <div className="site-header-inner">
            <img src={iconUrl} alt="NPB チーム成績" className="site-icon" />
            <div>
              <h1>
                NPB チーム成績
                {season?.year ? ` ${season.year}` : ""}
              </h1>
              <p>
                {season?.isPreviousSeason
                  ? `開幕前のため、前年度（${season.year}年）の結果を表示しています`
                  : "試合結果から順位・レーティング・優勝確率を計算しています"}
              </p>
            </div>
          </div>
        </Container>
      </header>

      <Container className="page-body">
        <section className="panel">
          <h2>順位表</h2>
          <p className="panel-lead">
            勝率順です。差は首位とのゲーム差、残は残り試合数です。
          </p>
          <Standings leagues={leagues} error={error} />
        </section>

        <section className="panel">
          <h2>期待勝敗数</h2>
          <p className="panel-lead">
            現在のレーティングに基づく残り試合の期待勝敗です。
          </p>
          <Row>
            <Col md={6}>
              <h3>セ・リーグ</h3>
              <CsvTable
                file="standings_estimate_central.csv"
                teamOrder={centralOrder}
              />
            </Col>
            <Col md={6}>
              <h3>パ・リーグ</h3>
              <CsvTable
                file="standings_estimate_pacific.csv"
                teamOrder={pacificOrder}
              />
            </Col>
          </Row>
        </section>

        <section className="panel">
          <h2>最終順位確率（％）</h2>
          <p className="panel-lead">
            残り試合を10万回シミュレーションした最終順位の割合です。
          </p>
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
        </section>

        <section className="panel">
          <h2>対戦勝率（％）</h2>
          <p className="panel-lead">
            現状レーティングから見た、行のチームが列のチームに勝つ確率です。
          </p>
          <CsvTable
            file="win_prob.csv"
            heatmap
            teamOrder={allOrder}
            showRating
            rankColors={false}
          />
        </section>

        <section className="panel">
          <h2>レート推移</h2>
          <Suspense fallback={<p className="text-muted">読み込み中...</p>}>
            <RatingChart teamOrder={allOrder} />
          </Suspense>
        </section>
      </Container>
    </div>
  );
}

export default App;
