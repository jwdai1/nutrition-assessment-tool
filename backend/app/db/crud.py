"""CRUD operations for patients and assessments."""
from __future__ import annotations
from typing import Optional, List

from sqlalchemy.orm import Session

from app.db.models import PatientModel, AssessmentModel
from app.schemas.patient import PatientCreate, PatientUpdate
from app.schemas.assessment import AssessmentCreate
from app.core import logic
from app.core.recommendations import get_recommendations, should_show_isocal


# --- Patients ---

def create_patient(db: Session, data: PatientCreate) -> PatientModel:
    patient = PatientModel(**data.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def get_patient(db: Session, patient_id: int) -> Optional[PatientModel]:
    return db.query(PatientModel).filter(PatientModel.id == patient_id).first()


def get_all_patients(db: Session) -> List[PatientModel]:
    return db.query(PatientModel).order_by(PatientModel.updated_at.desc()).all()


def search_patients(db: Session, query: str) -> List[PatientModel]:
    like = "%{}%".format(query)
    return (
        db.query(PatientModel)
        .filter(
            PatientModel.patient_code.ilike(like)
            | PatientModel.name.ilike(like)
        )
        .order_by(PatientModel.updated_at.desc())
        .all()
    )


def update_patient(db: Session, patient_id: int, data: PatientUpdate) -> Optional[PatientModel]:
    patient = get_patient(db, patient_id)
    if not patient:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    return patient


def delete_patient(db: Session, patient_id: int) -> bool:
    patient = get_patient(db, patient_id)
    if not patient:
        return False
    db.delete(patient)
    db.commit()
    return True


def patient_code_exists(db: Session, code: str, exclude_id: Optional[int] = None) -> bool:
    query = db.query(PatientModel).filter(PatientModel.patient_code == code)
    if exclude_id is not None:
        query = query.filter(PatientModel.id != exclude_id)
    return query.first() is not None


# --- Assessments ---

def create_assessment(db: Session, data: AssessmentCreate) -> AssessmentModel:
    mna = data.mna
    glim = data.glim

    bmi = logic.calc_bmi(data.weight_kg, data.height_cm)
    wl_pct_3m = logic.calc_weight_loss_pct(data.weight_kg, data.weight_3m_kg)
    wl_pct_6m = logic.calc_weight_loss_pct(data.weight_kg, data.weight_6m_kg)

    mna_answers = [mna.q_a, mna.q_b, mna.q_c, mna.q_d, mna.q_e, mna.q_f]
    mna_total = sum(a for a in mna_answers if a is not None) if all(a is not None for a in mna_answers) else None
    mna_interp = logic.interpret_mna_sf_score(mna_total)
    mna_category = mna_interp["category"] if mna_interp["category"] != "unknown" else None

    glim_diagnosed = None
    glim_severity = None
    if mna_total is not None and mna_total < 12:
        glim_result = logic.calc_glim_severity(
            glim_weight_loss=bool(glim.weight_loss),
            glim_low_bmi=bool(glim.low_bmi),
            glim_muscle=glim.muscle,
            glim_intake=bool(glim.intake),
            glim_inflam=bool(glim.inflam),
            glim_chronic=bool(glim.chronic),
            age=data.age_at_assess,
            bmi=bmi,
            wl_pct_3m=wl_pct_3m,
            wl_pct_6m=wl_pct_6m,
        )
        glim_diagnosed = 1 if glim_result["diagnosed"] else 0
        glim_severity = glim_result.get("severity")

    assessment = AssessmentModel(
        patient_id=data.patient_id,
        assess_date=data.assess_date,
        age_at_assess=data.age_at_assess,
        height_cm=data.height_cm,
        weight_kg=data.weight_kg,
        weight_3m_kg=data.weight_3m_kg,
        weight_6m_kg=data.weight_6m_kg,
        cc_cm=data.cc_cm,
        bmi=bmi,
        wl_pct_3m=wl_pct_3m,
        wl_pct_6m=wl_pct_6m,
        mna_q_a=mna.q_a,
        mna_q_b=mna.q_b,
        mna_q_c=mna.q_c,
        mna_q_d=mna.q_d,
        mna_q_e=mna.q_e,
        mna_q_f=mna.q_f,
        mna_total=mna_total,
        mna_category=mna_category,
        glim_weight_loss=glim.weight_loss,
        glim_low_bmi=glim.low_bmi,
        glim_muscle=glim.muscle,
        glim_intake=glim.intake,
        glim_inflam=glim.inflam,
        glim_chronic=glim.chronic,
        glim_diagnosed=glim_diagnosed,
        glim_severity=glim_severity,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def get_assessment(db: Session, assessment_id: int) -> Optional[AssessmentModel]:
    return db.query(AssessmentModel).filter(AssessmentModel.id == assessment_id).first()


def get_assessments_for_patient(db: Session, patient_id: int) -> List[AssessmentModel]:
    return (
        db.query(AssessmentModel)
        .filter(AssessmentModel.patient_id == patient_id)
        .order_by(AssessmentModel.assess_date.desc())
        .all()
    )


def delete_assessment(db: Session, assessment_id: int) -> bool:
    assessment = get_assessment(db, assessment_id)
    if not assessment:
        return False
    db.delete(assessment)
    db.commit()
    return True
