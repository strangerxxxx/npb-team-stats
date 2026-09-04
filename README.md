# NPB レーティング

NPB公式サイトから試合結果を取得し、Eloレーティングと順位予想を計算して可視化します。

```
scripts/scrape.py  →  data/scores/*.csv
scripts/compute.py →  public/data/*.csv  （ローカル）
                   →  S3 data/*          （本番）
src/               →  React（Vercel / GitHub Pages）
```

本番では Lambda が取得・計算し、フロントは S3 上の CSV/JSON を読みます。

## 構成

| パス | 役割 |
| --- | --- |
| `scripts/scrape.py` | NPB公式サイトから試合結果を取得 |
| `scripts/compute.py` | レーティング・順位予想を計算 |
| `sim/` | 順位シミュレーション（Rust） |
| `lambda/` | 定期更新用 Lambda（コンテナ） |
| `data/scores/` | 年度別の試合結果CSV（ローカル） |
| `public/data/` | 計算結果（ローカル開発用） |
| `src/` | React 可視化 |

## 使い方

```bash
pip install -r requirements.txt
python scripts/scrape.py          # 試合結果を取得（省略時は実行年。開幕前で試合がなければ前年度を表示）
python scripts/compute.py         # レーティング等を計算（開幕前は前年度）

順位シミュレーションは Rust（`sim/`）で実行します。初回の `compute.py` 実行時に `cargo build --release` されます。Rust が使えない場合は Python 実装に落ちます。
npm install
npm start
npm test
```

年度を指定する場合:

```bash
python scripts/scrape.py --year 2025
python scripts/compute.py --year 2025
```

`npm run update` で取得と計算をまとめて実行できます。

フロントを S3 のデータに向ける場合は、ビルド時に `VITE_DATA_BASE_URL` を設定します（末尾スラッシュなし、例: `https://npb-team-stats-data-<account>.s3.ap-northeast-1.amazonaws.com/data`）。未設定なら `public/data/` を使います。

## AWS（データ更新・公開）

取得・計算は Lambda、公開は S3（`ap-northeast-1`）です。EventBridge Scheduler が従来の GitHub Actions と同じ時間帯（JST、3/25〜11/15 は Lambda 側でも判定）で実行します。

Docker が使える環境で:

```bash
sam build
sam deploy --guided
```

スタック出力の `DataBaseUrl` を GitHub secret `VITE_DATA_BASE_URL` と、Vercel の Production 環境変数に設定してください。初回はコンソールから Lambda を `{"force": true}` で実行すると、S3 にデータが載ります。

## GitHub Pages / Vercel

リポジトリの Settings → Pages → Source を **GitHub Actions** にしてください。公開 URL は `https://<user>.github.io/<repo>/` です。

フロントのビルドとデプロイだけを Actions が行います。データの更新は Lambda です。
