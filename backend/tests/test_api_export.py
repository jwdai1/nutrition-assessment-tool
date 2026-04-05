"""Tests for CSV, Excel, and PDF export endpoints."""
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
def setup_data(client):
    resp = client.post("/api/patients", json={
        "patient_code": "PT-0001", "name": "テスト", "gender": "male"
    })
    pid = resp.json()["id"]
    resp = client.post("/api/assessments", json={
        "patient_id": pid, "assess_date": "2026-04-06", "age_at_assess": 75,
        "height_cm": 160.0, "weight_kg": 50.0,
        "mna": {"q_a": 1, "q_b": 0, "q_c": 1, "q_d": 0, "q_e": 1, "q_f": 1},
        "glim": {"weight_loss": 1, "intake": 1},
    })
    aid = resp.json()["id"]
    return pid, aid


def test_csv_export(client, setup_data):
    pid, _ = setup_data
    resp = client.get("/api/export/patients/{}/csv".format(pid))
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "評価日" in resp.text  # header row present
    assert "2026-04-06" in resp.text  # data row present


def test_excel_export(client, setup_data):
    pid, _ = setup_data
    resp = client.get("/api/export/patients/{}/excel".format(pid))
    assert resp.status_code == 200
    assert "spreadsheet" in resp.headers["content-type"]


def test_pdf_export(client, setup_data):
    _, aid = setup_data
    resp = client.get("/api/assessments/{}/pdf".format(aid))
    assert resp.status_code == 200
    # Accept either PDF or HTML fallback
    ct = resp.headers["content-type"]
    assert "pdf" in ct or "html" in ct
