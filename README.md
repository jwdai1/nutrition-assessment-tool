# 低栄養診断ツール（MNA-SF / GLIM）

MNA-SF スクリーニングと GLIM 基準による低栄養診断・重症度評価を行う Web アプリケーションです。  
GLIM 低栄養診断時にネスレ「アイソカル® 100」の製品推奨と購買導線を提供します。

---

## アーキテクチャ

```
Frontend (Next.js + Tailwind + shadcn/ui)
    │  REST API (JSON)
    ▼
Backend (FastAPI + SQLAlchemy)
    │
    ▼
SQLite (開発) / PostgreSQL (本番)
```

---

## 機能

- **患者管理** — 登録・編集・削除・検索
- **アセスメントウィザード** — ステップ形式で評価を入力
  - ステップ1: 患者基本情報（身長・体重・BMI自動計算）
  - ステップ2: MNA-SF スクリーニング（体重減少・BMI を自動推定）
  - ステップ3: GLIM 評価（MNA-SF < 12 の場合のみ）
- **診断結果** — 診断バナー、スコアサマリ、推奨アクション
- **アイソカル® 100 推奨** — GLIM 低栄養診断確定時に製品情報と購買リンクを表示
- **経時変化グラフ** — 体重・BMI・MNA スコアの推移
- **評価履歴** — 患者ごとの評価記録一覧
- **エクスポート** — PDF / CSV / Excel 出力

---

## 動作環境

| 項目 | 要件 |
|------|------|
| バックエンド | Python 3.8+ |
| フロントエンド | Node.js 20+ |
| 主要ライブラリ | FastAPI, SQLAlchemy, Next.js, Tailwind CSS, shadcn/ui |

---

## セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/jwdai1/nutrition-assessment-tool.git
cd nutrition-assessment-tool
```

### 2. バックエンド

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API ドキュメント: http://localhost:8000/docs

### 3. フロントエンド

```bash
cd frontend
npm install
npm run dev
```

アプリ: http://localhost:3000

### 4. 環境変数（オプション）

**backend/.env:**
```
DATABASE_URL=sqlite:///./nutrition_tool.db
```

**frontend/.env.local:**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## ディレクトリ構成

```
nutrition-assessment-tool/
├── backend/
│   ├── app/
│   │   ├── main.py              FastAPI エントリポイント
│   │   ├── config.py            設定（アイソカル URL 等）
│   │   ├── core/
│   │   │   ├── logic.py         診断ロジック
│   │   │   └── recommendations.py  推奨アクション
│   │   ├── routers/
│   │   │   ├── patients.py      患者 API
│   │   │   ├── assessments.py   評価 API
│   │   │   ├── export.py        CSV / Excel
│   │   │   └── pdf.py           PDF 出力
│   │   ├── db/
│   │   │   ├── database.py      SQLAlchemy 設定
│   │   │   ├── models.py        ORM モデル
│   │   │   └── crud.py          CRUD 操作
│   │   └── schemas/             Pydantic スキーマ
│   ├── alembic/                 マイグレーション
│   └── tests/                   pytest テスト
├── frontend/
│   ├── app/                     Next.js App Router
│   ├── components/              UI コンポーネント
│   └── lib/api.ts               API クライアント
└── docs/                        設計書・計画書
```

---

## API エンドポイント

| メソッド | パス | 説明 |
|----------|------|------|
| GET | /api/patients | 患者一覧（?q= で検索） |
| POST | /api/patients | 患者登録 |
| GET | /api/patients/{id} | 患者詳細 |
| PUT | /api/patients/{id} | 患者編集 |
| DELETE | /api/patients/{id} | 患者削除 |
| GET | /api/patients/{id}/assessments | 評価履歴 |
| GET | /api/patients/{id}/assessments/chart | グラフデータ |
| POST | /api/assessments | 評価保存（診断実行） |
| GET | /api/assessments/{id} | 評価詳細 |
| GET | /api/assessments/{id}/pdf | PDF ダウンロード |
| GET | /api/export/patients/{id}/csv | CSV 出力 |
| GET | /api/export/patients/{id}/excel | Excel 出力 |

---

## テスト

```bash
cd backend
python -m pytest -v
```

---

## 免責事項

本ツールは臨床判断を**支援**するためのものです。診断・治療方針は必ず臨床医が総合的に判断してください。

- MNA® は Société des Produits Nestlé S.A. の登録商標です
- GLIM 基準: Cederholm T, et al. *JPEN J Parenter Enteral Nutr.* 2019;43(1):32-40.
