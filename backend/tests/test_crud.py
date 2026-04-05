"""Tests for CRUD operations."""
from __future__ import annotations
from app.db.crud import (
    create_patient, get_patient, get_all_patients, search_patients,
    update_patient, delete_patient, patient_code_exists,
    create_assessment, get_assessment, get_assessments_for_patient,
)
from app.schemas.patient import PatientCreate, PatientUpdate
from app.schemas.assessment import AssessmentCreate, MNAInput, GLIMInput


def test_create_and_get_patient(db):
    data = PatientCreate(patient_code="PT-0001", name="田中太郎", gender="male")
    patient = create_patient(db, data)
    assert patient.id is not None
    assert patient.patient_code == "PT-0001"
    fetched = get_patient(db, patient.id)
    assert fetched.name == "田中太郎"


def test_search_patients(db):
    create_patient(db, PatientCreate(patient_code="PT-0001", name="田中太郎", gender="male"))
    create_patient(db, PatientCreate(patient_code="PT-0002", name="鈴木花子", gender="female"))
    results = search_patients(db, "田中")
    assert len(results) == 1
    results = search_patients(db, "PT-000")
    assert len(results) == 2


def test_update_patient(db):
    patient = create_patient(db, PatientCreate(patient_code="PT-0001", name="旧名", gender="male"))
    updated = update_patient(db, patient.id, PatientUpdate(name="新名"))
    assert updated.name == "新名"


def test_delete_patient(db):
    patient = create_patient(db, PatientCreate(patient_code="PT-0001", name="テスト", gender="male"))
    delete_patient(db, patient.id)
    assert get_patient(db, patient.id) is None


def test_patient_code_exists(db):
    create_patient(db, PatientCreate(patient_code="PT-0001", name="テスト", gender="male"))
    assert patient_code_exists(db, "PT-0001") is True
    assert patient_code_exists(db, "PT-9999") is False


def test_create_assessment_with_diagnosis(db):
    patient = create_patient(db, PatientCreate(patient_code="PT-0001", name="テスト", gender="male"))
    data = AssessmentCreate(
        patient_id=patient.id,
        assess_date="2026-04-06",
        age_at_assess=75,
        height_cm=160.0,
        weight_kg=50.0,
        weight_3m_kg=55.0,
        mna=MNAInput(q_a=1, q_b=0, q_c=1, q_d=0, q_e=1, q_f=1),
        glim=GLIMInput(weight_loss=1, intake=1),
    )
    assessment = create_assessment(db, data)
    assert assessment.id is not None
    assert assessment.bmi is not None
    assert assessment.mna_total == 4
    assert assessment.glim_diagnosed == 1


def test_create_assessment_normal(db):
    patient = create_patient(db, PatientCreate(patient_code="PT-0001", name="テスト", gender="male"))
    data = AssessmentCreate(
        patient_id=patient.id,
        assess_date="2026-04-06",
        age_at_assess=75,
        height_cm=160.0,
        weight_kg=60.0,
        mna=MNAInput(q_a=2, q_b=3, q_c=2, q_d=2, q_e=2, q_f=3),
        glim=GLIMInput(),
    )
    assessment = create_assessment(db, data)
    assert assessment.mna_total == 14
    assert assessment.mna_category == "normal"
    assert assessment.glim_diagnosed is None


def test_get_assessments_for_patient(db):
    patient = create_patient(db, PatientCreate(patient_code="PT-0001", name="テスト", gender="male"))
    for date in ["2026-01-01", "2026-02-01", "2026-03-01"]:
        create_assessment(db, AssessmentCreate(
            patient_id=patient.id, assess_date=date, age_at_assess=75,
            height_cm=160.0, weight_kg=50.0,
            mna=MNAInput(q_a=2, q_b=3, q_c=2, q_d=2, q_e=2, q_f=3),
            glim=GLIMInput(),
        ))
    assessments = get_assessments_for_patient(db, patient.id)
    assert len(assessments) == 3
    assert assessments[0].assess_date == "2026-03-01"
