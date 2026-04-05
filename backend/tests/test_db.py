from app.db.models import PatientModel


def test_create_patient(db):
    patient = PatientModel(
        patient_code="PT-0001",
        name="テスト太郎",
        gender="male",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    assert patient.id is not None
    assert patient.patient_code == "PT-0001"
