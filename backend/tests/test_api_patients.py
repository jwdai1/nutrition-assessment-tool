"""Tests for patient API endpoints."""
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


def test_create_patient(client):
    resp = client.post("/api/patients", json={
        "patient_code": "PT-0001", "name": "田中太郎", "gender": "male"
    })
    assert resp.status_code == 201
    assert resp.json()["patient_code"] == "PT-0001"


def test_get_patients(client):
    client.post("/api/patients", json={"patient_code": "PT-0001", "name": "A", "gender": "male"})
    client.post("/api/patients", json={"patient_code": "PT-0002", "name": "B", "gender": "female"})
    resp = client.get("/api/patients")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_search_patients(client):
    client.post("/api/patients", json={"patient_code": "PT-0001", "name": "田中太郎", "gender": "male"})
    client.post("/api/patients", json={"patient_code": "PT-0002", "name": "鈴木花子", "gender": "female"})
    resp = client.get("/api/patients?q=田中")
    assert len(resp.json()) == 1


def test_update_patient(client):
    r = client.post("/api/patients", json={"patient_code": "PT-0001", "name": "旧名", "gender": "male"})
    pid = r.json()["id"]
    resp = client.put("/api/patients/{}".format(pid), json={"name": "新名"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "新名"


def test_delete_patient(client):
    r = client.post("/api/patients", json={"patient_code": "PT-0001", "name": "テスト", "gender": "male"})
    pid = r.json()["id"]
    resp = client.delete("/api/patients/{}".format(pid))
    assert resp.status_code == 204
    resp = client.get("/api/patients/{}".format(pid))
    assert resp.status_code == 404


def test_duplicate_code(client):
    client.post("/api/patients", json={"patient_code": "PT-0001", "name": "A", "gender": "male"})
    resp = client.post("/api/patients", json={"patient_code": "PT-0001", "name": "B", "gender": "female"})
    assert resp.status_code == 409
