"""CSV and Excel export endpoints."""
from __future__ import annotations
import csv
import io
from typing import List, Tuple
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud

router = APIRouter(prefix="/api/export", tags=["export"])

CSV_COLUMNS: List[Tuple[str, str]] = [
    ("assess_date", "評価日"),
    ("age_at_assess", "年齢"),
    ("height_cm", "身長(cm)"),
    ("weight_kg", "体重(kg)"),
    ("bmi", "BMI"),
    ("wl_pct_3m", "体重減少率3M(%)"),
    ("wl_pct_6m", "体重減少率6M(%)"),
    ("mna_total", "MNA-SF合計"),
    ("mna_category", "MNA判定"),
    ("glim_diagnosed", "GLIM診断"),
    ("glim_severity", "GLIM重症度"),
]


@router.get("/patients/{patient_id}/csv")
def export_csv(patient_id: int, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    assessments = crud.get_assessments_for_patient(db, patient_id)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([col[1] for col in CSV_COLUMNS])
    for a in assessments:
        writer.writerow([getattr(a, col[0]) for col in CSV_COLUMNS])

    buf.seek(0)
    filename = "assessments_{}.csv".format(patient.patient_code)
    return StreamingResponse(
        buf,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="{}"'.format(filename)},
    )


@router.get("/patients/{patient_id}/excel")
def export_excel(patient_id: int, db: Session = Depends(get_db)):
    from openpyxl import Workbook

    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    assessments = crud.get_assessments_for_patient(db, patient_id)

    wb = Workbook()
    ws = wb.active
    ws.title = "評価履歴"
    ws.append([col[1] for col in CSV_COLUMNS])
    for a in assessments:
        ws.append([getattr(a, col[0]) for col in CSV_COLUMNS])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = "assessments_{}.xlsx".format(patient.patient_code)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="{}"'.format(filename)},
    )
