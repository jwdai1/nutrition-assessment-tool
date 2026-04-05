"""Patient CRUD API endpoints."""
from __future__ import annotations
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("", response_model=List[PatientResponse])
def list_patients(q: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if q:
        return crud.search_patients(db, q)
    return crud.get_all_patients(db)


@router.post("", response_model=PatientResponse, status_code=201)
def create_patient(data: PatientCreate, db: Session = Depends(get_db)):
    if crud.patient_code_exists(db, data.patient_code):
        raise HTTPException(status_code=409, detail="Patient code already exists")
    return crud.create_patient(db, data)


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(patient_id: int, data: PatientUpdate, db: Session = Depends(get_db)):
    if data.patient_code and crud.patient_code_exists(db, data.patient_code, exclude_id=patient_id):
        raise HTTPException(status_code=409, detail="Patient code already exists")
    patient = crud.update_patient(db, patient_id, data)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.delete("/{patient_id}", status_code=204)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    if not crud.delete_patient(db, patient_id):
        raise HTTPException(status_code=404, detail="Patient not found")
