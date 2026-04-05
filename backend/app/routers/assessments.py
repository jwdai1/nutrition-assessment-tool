"""Assessment API endpoints."""
from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.schemas.assessment import (
    AssessmentCreate, AssessmentResponse, IsocalRecommendation,
    ChartResponse, ChartDataPoint,
)
from app.core.logic import interpret_mna_sf_score, calc_glim_severity
from app.core.recommendations import get_recommendations, should_show_isocal
from app.config import ISOCAL_PRODUCT

router = APIRouter(tags=["assessments"])


def _build_response(assessment) -> dict:
    a = assessment
    mna_interp = interpret_mna_sf_score(a.mna_total)

    reasons = []
    if a.glim_diagnosed and a.mna_total is not None and a.mna_total < 12:
        glim_result = calc_glim_severity(
            glim_weight_loss=bool(a.glim_weight_loss),
            glim_low_bmi=bool(a.glim_low_bmi),
            glim_muscle=a.glim_muscle or "none",
            glim_intake=bool(a.glim_intake),
            glim_inflam=bool(a.glim_inflam),
            glim_chronic=bool(a.glim_chronic),
            age=a.age_at_assess,
            bmi=a.bmi,
            wl_pct_3m=a.wl_pct_3m,
            wl_pct_6m=a.wl_pct_6m,
        )
        reasons = glim_result.get("reasons", [])

    recs = get_recommendations(
        a.mna_category,
        bool(a.glim_diagnosed) if a.glim_diagnosed is not None else None,
        a.glim_severity,
    )

    show_isocal = should_show_isocal(
        bool(a.glim_diagnosed) if a.glim_diagnosed is not None else None
    )

    isocal = IsocalRecommendation(
        show=show_isocal,
        **(ISOCAL_PRODUCT if show_isocal else {}),
    )

    return {
        **{c.name: getattr(a, c.name) for c in a.__table__.columns},
        "recommendations": recs,
        "reasons": reasons,
        "isocal_recommendation": isocal,
    }


@router.post("/api/assessments", response_model=AssessmentResponse, status_code=201)
def create_assessment(data: AssessmentCreate, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, data.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    assessment = crud.create_assessment(db, data)
    return _build_response(assessment)


@router.get("/api/assessments/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    assessment = crud.get_assessment(db, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return _build_response(assessment)


@router.get("/api/patients/{patient_id}/assessments", response_model=List[AssessmentResponse])
def list_assessments(patient_id: int, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    assessments = crud.get_assessments_for_patient(db, patient_id)
    return [_build_response(a) for a in assessments]


@router.get("/api/patients/{patient_id}/assessments/chart", response_model=ChartResponse)
def chart_data(patient_id: int, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    assessments = crud.get_assessments_for_patient(db, patient_id)
    data = [
        ChartDataPoint(
            assess_date=a.assess_date,
            weight_kg=a.weight_kg,
            bmi=a.bmi,
            mna_total=a.mna_total,
        )
        for a in reversed(assessments)
    ]
    return ChartResponse(data=data)
