# NPB レーティング

NPB公式サイトから試合結果を取得し、Eloレーティングと順位予想を計算して可視化します。

```
data/scores/*.csv   →  scripts/compute.py  →  public/data/*.csv  →  React
         ↑
 scripts/scrape.py
```

## 構成

| パス | 役割 |
| --- | --- |
| `scripts/scrape.py` | NPB公式サイトから試合結果を取得 |
| `scripts/compute.py` | レーティング・順位予想を計算 |
| `sim/` | 順位シミュレーション（Rust） |
| `data/scores/` | 年度別の試合結果CSV |
| `public/data/` | 計算結果（フロントが参照） |
| `src/` | React 可視化 |

以前の `npb_scrape.py` は `scripts/scrape.py`、`r.py` は `scripts/compute.py` に移しました。

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

## GitHub Pages

リポジトリの Settings → Pages → Source を **GitHub Actions** にしてください。公開 URL は `https://<user>.github.io/<repo>/` です。

Actions が試合結果の取得・計算・デプロイまで行います。

- 期間: 3/25〜11/15
- 時刻: 21:00〜27:00 JST（翌 3:00 まで）の毎時
- `main` / `master` への push と手動実行（Run workflow）でもデプロイします
