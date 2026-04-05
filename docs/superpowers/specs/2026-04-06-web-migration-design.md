# 低栄養診断ツール Web版移行 設計書

## 概要

MNA-SF / GLIM 基準による低栄養診断 PySide6 デスクトップアプリを、React + FastAPI の Web アプリに転換する。GLIM 低栄養診断確定時にネスレ「アイソカル 100」の推奨表示と購買導線を組み込む。

### ビジネスコンテキスト

- 病院向けに提供する臨床ツール + 自社製品プロモーション
- 診断フローの出口にアイソカル 100 の推奨と購買ページ/ブランドサイトへのリンクを設置
- 操作性と視覚性が重要（お客様＝病院スタッフが利用）

---

## システムアーキテクチャ

```
Browser (Next.js + Tailwind + shadcn/ui)
  ├── /patients          患者管理
  ├── /patients/[id]     患者詳細+履歴+経時グラフ
  ├── /assess/new        評価ウィザード（4ステップ）
  └── /assess/[id]       結果画面+推奨+アイソカル推奨
        │
        │ REST API (JSON)
        ▼
FastAPI
  ├── routers/           API エンドポイント
  ├── core/logic.py      既存診断ロジック移植
  ├── core/recommendations.py  推奨+アイソカル判定
  ├── db/                SQLAlchemy + Alembic
  └── schemas/           Pydantic v2
        │
        ▼
SQLite (開発) / PostgreSQL (本番)
```

---

## 画面構成

| # | 画面 | パス | 主な要素 |
|---|------|------|----------|
| 1 | 患者一覧 | `/patients` | 検索バー、患者カード/テーブル、追加ボタン |
| 2 | 患者登録/編集 | モーダル | フォーム（ID・氏名・性別・生年月日・備考） |
| 3 | 患者詳細 | `/patients/[id]` | 基本情報、評価履歴テーブル、経時グラフ、新規評価ボタン |
| 4 | ウィザード Step1 | `/assess/new?patient=[id]` | 評価日・年齢・身長・体重・過去体重・CC |
| 5 | ウィザード Step2 | 同上（ステッパー） | MNA-SF 問A〜F、スコアバー |
| 6 | ウィザード Step3 | 同上 | GLIM 表現型+病因基準（MNA<12時のみ） |
| 7 | 結果画面 | `/assess/[id]` | 診断バナー、スコアサマリ、推奨アクション、アイソカル推奨（低栄養時）、PDF出力ボタン |

### ユーザーフロー

```
[患者一覧] → [患者詳細/履歴] → [新規評価ウィザード] → [結果画面]
                                                          │
                                                    GLIM低栄養時
                                                          ↓
                                                   アイソカル100推奨
                                                   バナー+購買リンク
```

### 経時グラフ（患者詳細画面）

- Recharts で体重・BMI・MNA スコアの推移を折れ線グラフ表示
- X軸: 評価日、Y軸: 各値

---

## アイソカル 100 推奨表示

GLIM 低栄養診断が確定した場合のみ結果画面に表示。

### バナー内容

- 製品画像 + 製品名「アイソカル 100」
- 「100mlで200kcal、たんぱく質8g、ビタミン13種・ミネラル13種」
- 許可表示全文:

> 本品は、食事として摂取すべき栄養素をバランスよく配合した総合栄養食品です。通常の食事で十分な栄養を摂ることができない方や低栄養の方の栄養補給に適しています。
>
> 医師、管理栄養士等のご指導に従って使用してください。本品は栄養療法の素材として適するものであって、多く摂取することによって疾病が治癒するものではありません。

**注: 許可表示の文言は正式な社内原文で最終確認・差し替えが必要。**

- CTA ボタン:
  - 「製品について詳しく」→ ブランドサイト
  - 「ご購入はこちら」→ 購買ページ

---

## データ設計

既存スキーマをそのまま移行。変更なし。

### patients テーブル

| カラム | 型 | 制約 |
|--------|-----|------|
| id | INTEGER | PK, AUTO |
| patient_code | TEXT | UNIQUE, NOT NULL |
| name | TEXT | |
| gender | TEXT | NOT NULL ('male'/'female'/'other') |
| birth_date | TEXT | YYYY-MM-DD |
| notes | TEXT | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### assessments テーブル

| カラム | 型 | 制約 |
|--------|-----|------|
| id | INTEGER | PK, AUTO |
| patient_id | INTEGER | FK → patients.id CASCADE |
| assess_date | TEXT | NOT NULL |
| age_at_assess | INTEGER | NOT NULL |
| height_cm | FLOAT | NOT NULL |
| weight_kg | FLOAT | NOT NULL |
| weight_3m_kg | FLOAT | nullable |
| weight_6m_kg | FLOAT | nullable |
| cc_cm | FLOAT | nullable |
| bmi | FLOAT | |
| wl_pct_3m | FLOAT | |
| wl_pct_6m | FLOAT | |
| mna_q_a〜q_f | INTEGER | 各問の回答 |
| mna_total | INTEGER | |
| mna_category | TEXT | 'normal'/'risk'/'severe' |
| glim_weight_loss | INTEGER | 0/1 |
| glim_low_bmi | INTEGER | 0/1 |
| glim_muscle | TEXT | 'none'/'mild'/'severe' |
| glim_intake | INTEGER | 0/1 |
| glim_inflam | INTEGER | 0/1 |
| glim_chronic | INTEGER | 0/1 |
| glim_diagnosed | INTEGER | 0/1 |
| glim_severity | TEXT | null/'stage1'/'stage2' |
| created_at | TIMESTAMP | |

将来の認証追加時に `users` テーブルと `assessments.user_id` を追加する想定。

---

## API 設計

### エンドポイント

```
GET    /api/patients                       患者一覧（検索クエリ対応）
POST   /api/patients                       患者登録
GET    /api/patients/{id}                  患者詳細
PUT    /api/patients/{id}                  患者編集
DELETE /api/patients/{id}                  患者削除

GET    /api/patients/{id}/assessments      評価履歴一覧
GET    /api/patients/{id}/assessments/chart グラフ用データ

POST   /api/assessments                    評価保存（診断ロジック実行+結果返却）
GET    /api/assessments/{id}               評価詳細

GET    /api/assessments/{id}/pdf           PDF ダウンロード
GET    /api/export/patients/{id}/csv       CSV 出力
GET    /api/export/patients/{id}/excel     Excel 出力
```

### POST /api/assessments レスポンス例

```json
{
  "id": 42,
  "mna_total": 7,
  "mna_category": "severe",
  "glim_diagnosed": true,
  "glim_severity": "stage1",
  "reasons": ["3ヶ月体重減少率 8.2%（Stage 1基準: 5〜10%）"],
  "recommendations": ["中等度低栄養（Stage 1）：管理栄養士による栄養介入計画を策定してください。"],
  "isocal_recommendation": {
    "show": true,
    "product_name": "アイソカル® 100",
    "description": "100mlで200kcal、たんぱく質8g、ビタミン13種・ミネラル13種",
    "permitted_claim": "（許可表示全文）",
    "brand_url": "https://healthscienceshop.nestle.jp/blogs/isocal/isocal-100-index",
    "purchase_url": "https://healthscienceshop.nestle.jp/products/isocal-100"
  }
}
```

製品情報はバックエンド側の設定ファイルで管理（URL 変更時にフロント再デプロイ不要）。

---

## 診断ロジック

既存 `logic.py` をそのまま移植。臨床基準との整合性は検証済み。

### 臨床フロー

```
MNA-SF（スクリーニング）
  ├── 12-14点 → 栄養良好 → 終了
  └── 0-11点 → 低栄養リスク/可能性
        ↓
      GLIM 評価（診断）
        ├── 表現型基準（体重減少/低BMI/筋量低下）≥1
        │   AND
        ├── 病因基準（摂取低下/急性炎症/慢性炎症）≥1
        │   → 低栄養確定 → Stage 判定 → アイソカル推奨表示
        └── どちらか不充足 → 低栄養未診断
```

### 関数一覧（移植対象）

| 関数 | 用途 |
|------|------|
| calc_bmi | BMI 計算 |
| calc_weight_loss_pct | 体重減少率 |
| is_low_bmi_glim | GLIM 低BMI 判定（アジア基準） |
| is_low_bmi_severe | GLIM Stage 2 BMI 判定 |
| interpret_mna_sf_score | MNA-SF スコア解釈 |
| interpret_weight_loss_glim | GLIM 体重減少解釈 |
| calc_glim_severity | GLIM 診断+重症度判定 |
| auto_estimate_mna_q_b | MNA-SF 問B 自動推定 |
| auto_estimate_mna_q_f_bmi | MNA-SF 問F BMI 自動推定 |
| auto_estimate_mna_q_f_cc | MNA-SF 問F CC 自動推定 |
| get_recommendations | 推奨アクション生成 |
| should_show_isocal | アイソカル推奨表示判定（新規追加） |

---

## 技術スタック

### バックエンド

| 項目 | 選定 |
|------|------|
| フレームワーク | FastAPI |
| ORM | SQLAlchemy 2.0 + Alembic |
| スキーマ | Pydantic v2 |
| DB | SQLite（開発）/ PostgreSQL（本番） |
| PDF | WeasyPrint |
| Excel | openpyxl |

### フロントエンド

| 項目 | 選定 |
|------|------|
| フレームワーク | Next.js 14 (App Router) |
| UI | Tailwind CSS + shadcn/ui |
| チャート | Recharts |
| フォーム | React Hook Form + Zod |
| 状態管理 | React Server Components + クライアント最小限 |

### 開発基盤

| 項目 | 選定 |
|------|------|
| テスト（BE） | pytest |
| テスト（FE） | Vitest + Testing Library |
| リンター | Ruff / ESLint + Prettier |
| 型チェック | mypy / TypeScript strict |

---

## ディレクトリ構成

```
nutrition-assessment-tool/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py            アイソカルURL等の設定
│   │   ├── core/
│   │   │   ├── logic.py         既存ロジック移植
│   │   │   └── recommendations.py
│   │   ├── routers/
│   │   │   ├── patients.py
│   │   │   ├── assessments.py
│   │   │   ├── export.py
│   │   │   └── pdf.py
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   ├── models.py
│   │   │   └── crud.py
│   │   └── schemas/
│   │       ├── patient.py
│   │       └── assessment.py
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── patients/
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   └── assess/
│   │       ├── new/page.tsx
│   │       └── [id]/page.tsx
│   ├── components/
│   │   ├── ui/                  shadcn/ui
│   │   ├── patient-form.tsx
│   │   ├── wizard/
│   │   │   ├── step-1.tsx
│   │   │   ├── step-2-mna.tsx
│   │   │   ├── step-3-glim.tsx
│   │   │   └── step-4-result.tsx
│   │   ├── assessment-chart.tsx
│   │   └── isocal-banner.tsx
│   ├── lib/api.ts
│   ├── package.json
│   └── tsconfig.json
├── docs/superpowers/specs/
└── README.md
```

---

## スコープ外（将来対応）

- ユーザー認証（構造的には対応可能な設計）
- ダッシュボード（統計サマリ）
- 複数施設対応

---

## MVP 機能一覧

1. 患者管理（登録・編集・削除・検索）
2. MNA-SF / GLIM 評価ウィザード（4ステップ）
3. 結果画面 + GLIM 低栄養時アイソカル 100 推奨バナー + 購買リンク
4. 評価履歴一覧
5. 経時変化グラフ（体重・BMI・MNA 推移）
6. PDF 出力
7. CSV / Excel エクスポート
