"""Tests for assessment API endpoints."""
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, get_db
from tests.conftest import engine, TestingSessionLocal


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def patient_id(client):
    resp = client.post("/api/patients", json={
        "patient_code": "PT-0001", "name": "テスト", "gender": "male"
    })
    return resp.json()["id"]


def test_create_assessment_diagnosed(client, patient_id):
    resp = client.post("/api/assessments", json={
        "patient_id": patient_id, "assess_date": "2026-04-06", "age_at_assess": 75,
        "height_cm": 160.0, "weight_kg": 50.0, "weight_3m_kg": 55.0,
        "mna": {"q_a": 1, "q_b": 0, "q_c": 1, "q_d": 0, "q_e": 1, "q_f": 1},
        "glim": {"weight_loss": 1, "intake": 1},
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["glim_diagnosed"] == 1
    assert data["isocal_recommendation"]["show"] is True
    assert "アイソカル" in data["isocal_recommendation"]["product_name"]


def test_create_assessment_normal(client, patient_id):
    resp = client.post("/api/assessments", json={
        "patient_id": patient_id, "assess_date": "2026-04-06", "age_at_assess": 75,
        "height_cm": 160.0, "weight_kg": 60.0,
        "mna": {"q_a": 2, "q_b": 3, "q_c": 2, "q_d": 2, "q_e": 2, "q_f": 3},
        "glim": {},
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["mna_category"] == "normal"
    assert data["isocal_recommendation"]["show"] is False


def test_get_assessment(client, patient_id):
    r = client.post("/api/assessments", json={
        "patient_id": patient_id, "assess_date": "2026-04-06", "age_at_assess": 75,
        "height_cm": 160.0, "weight_kg": 50.0,
        "mna": {"q_a": 1, "q_b": 0, "q_c": 1, "q_d": 0, "q_e": 1, "q_f": 1},
        "glim": {"weight_loss": 1, "intake": 1},
    })
    aid = r.json()["id"]
    resp = client.get("/api/assessments/{}".format(aid))
    assert resp.status_code == 200


def test_list_assessments(client, patient_id):
    client.post("/api/assessments", json={
        "patient_id": patient_id, "assess_date": "2026-04-06", "age_at_assess": 75,
        "height_cm": 160.0, "weight_kg": 50.0,
        "mna": {"q_a": 2, "q_b": 3, "q_c": 2, "q_d": 2, "q_e": 2, "q_f": 3},
        "glim": {},
    })
    resp = client.get("/api/patients/{}/assessments".format(patient_id))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_chart_data(client, patient_id):
    client.post("/api/assessments", json={
        "patient_id": patient_id, "assess_date": "2026-04-06", "age_at_assess": 75,
        "height_cm": 160.0, "weight_kg": 50.0,
        "mna": {"q_a": 2, "q_b": 3, "q_c": 2, "q_d": 2, "q_e": 2, "q_f": 3},
        "glim": {},
    })
    resp = client.get("/api/patients/{}/assessments/chart".format(patient_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert "weight_kg" in data[0]
