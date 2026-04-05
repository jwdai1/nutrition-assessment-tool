"""PDF export endpoint."""
from __future__ import annotations
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.core.logic import interpret_mna_sf_score, calc_glim_severity
from app.core.recommendations import get_recommendations

router = APIRouter(tags=["pdf"])

PDF_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: "Hiragino Sans", "Yu Gothic", sans-serif; font-size: 11px; color: #111827; margin: 20mm; }}
  h1 {{ color: #1a56a4; font-size: 16px; border-bottom: 2px solid #1a56a4; padding-bottom: 4px; }}
  h2 {{ color: #1a56a4; font-size: 13px; margin-top: 16px; border-bottom: 1px solid #d1d5db; padding-bottom: 2px; }}
  .banner {{ padding: 10px 14px; border-radius: 6px; font-weight: bold; font-size: 13px; margin: 12px 0; }}
  .banner-normal {{ background: #e6f5ec; border: 2px solid #1a7a4a; color: #1a7a4a; }}
  .banner-risk {{ background: #fef3c7; border: 2px solid #b45309; color: #b45309; }}
  .banner-mal {{ background: #fdecea; border: 2px solid #c0392b; color: #c0392b; }}
  table {{ width: 100%; border-collapse: collapse; margin: 8px 0; }}
  td {{ padding: 3px 8px; }}
  td.label {{ color: #6b7280; width: 35%; }}
  td.value {{ font-weight: bold; }}
  .rec {{ background: #fef3c7; border: 1px solid #fcd34d; border-radius: 4px; padding: 6px 10px; margin: 4px 0; }}
  .rec-severe {{ background: #fdecea; border-color: #fca5a5; }}
  .footer {{ margin-top: 20px; padding-top: 8px; border-top: 1px solid #d1d5db; font-size: 9px; color: #6b7280; }}
</style>
</head>
<body>
<h1>低栄養診断レポート（MNA-SF / GLIM）</h1>
<h2>患者情報</h2>
<table>
  <tr><td class="label">患者ID</td><td class="value">{patient_code}</td></tr>
  <tr><td class="label">氏名</td><td class="value">{name}</td></tr>
  <tr><td class="label">評価日</td><td class="value">{assess_date}</td></tr>
  <tr><td class="label">性別 / 年齢</td><td class="value">{gender_label} / {age}歳</td></tr>
  <tr><td class="label">身長 / 体重</td><td class="value">{height}cm / {weight}kg</td></tr>
  <tr><td class="label">BMI</td><td class="value">{bmi}</td></tr>
</table>
<div class="banner {banner_class}">{banner_text}</div>
<h2>MNA-SF スコア</h2>
<p><strong>{mna_total} / 14点 — {mna_label}</strong></p>
{glim_section}
<h2>推奨アクション</h2>
{recommendations_html}
<div class="footer">
このツールは臨床判断を支援するためのものです。MNA&reg; は Nestl&eacute; の登録商標です。
</div>
</body>
</html>"""


@router.get("/api/assessments/{assessment_id}/pdf")
def export_pdf(assessment_id: int, db: Session = Depends(get_db)):
    a = crud.get_assessment(db, assessment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    patient = crud.get_patient(db, a.patient_id)

    mna_interp = interpret_mna_sf_score(a.mna_total)
    skip_glim = a.mna_total is not None and a.mna_total >= 12

    if skip_glim:
        banner_class, banner_text = "banner-normal", "栄養良好（MNA-SF ≥12）"
    elif not a.glim_diagnosed:
        banner_class, banner_text = "banner-risk", "低栄養非該当（要観察）"
    else:
        sev = a.glim_severity
        banner_class = "banner-mal"
        banner_text = "低栄養（Stage 2: 高度）" if sev == "stage2" else "低栄養（Stage 1: 中等度）"

    glim_section = ""
    if not skip_glim and a.glim_diagnosed:
        glim_result = calc_glim_severity(
            bool(a.glim_weight_loss), bool(a.glim_low_bmi), a.glim_muscle or "none",
            bool(a.glim_intake), bool(a.glim_inflam), bool(a.glim_chronic),
            a.age_at_assess, a.bmi, a.wl_pct_3m, a.wl_pct_6m,
        )
        reasons_html = "".join("<li>{}</li>".format(r) for r in glim_result.get("reasons", []))
        glim_section = "<h2>GLIM 評価結果</h2><ul>{}</ul>".format(reasons_html)

    recs = get_recommendations(
        a.mna_category,
        bool(a.glim_diagnosed) if a.glim_diagnosed is not None else None,
        a.glim_severity,
    )
    rec_class = "rec-severe" if a.glim_severity == "stage2" else "rec"
    recommendations_html = "".join('<div class="{}">{}</div>'.format(rec_class, r) for r in recs)

    gender_map = {"male": "男性", "female": "女性", "other": "その他"}
    html_str = PDF_HTML_TEMPLATE.format(
        patient_code=patient.patient_code,
        name=patient.name or "—",
        assess_date=a.assess_date,
        gender_label=gender_map.get(patient.gender, patient.gender),
        age=a.age_at_assess,
        height="{:.1f}".format(a.height_cm),
        weight="{:.1f}".format(a.weight_kg),
        bmi="{:.1f}".format(a.bmi) if a.bmi else "—",
        banner_class=banner_class,
        banner_text=banner_text,
        mna_total=a.mna_total if a.mna_total is not None else "—",
        mna_label=mna_interp.get("label", ""),
        glim_section=glim_section,
        recommendations_html=recommendations_html,
    )

    # Try WeasyPrint first, fallback to HTML response
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_str).write_pdf()
        buf = io.BytesIO(pdf_bytes)
        media_type = "application/pdf"
    except (ImportError, OSError):
        # WeasyPrint not available — return HTML as fallback
        buf = io.BytesIO(html_str.encode("utf-8"))
        media_type = "text/html; charset=utf-8"

    filename = "report_{}_{}.pdf".format(patient.patient_code, a.assess_date)
    return StreamingResponse(
        buf,
        media_type=media_type,
        headers={"Content-Disposition": 'attachment; filename="{}"'.format(filename)},
    )
