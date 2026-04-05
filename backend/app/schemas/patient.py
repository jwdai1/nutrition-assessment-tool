"""Pydantic schemas for Patient API."""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PatientCreate(BaseModel):
    patient_code: str = Field(..., min_length=1, max_length=50)
    name: str = ""
    gender: str = Field(..., pattern="^(male|female|other)$")
    birth_date: Optional[str] = None
    notes: str = ""


class PatientUpdate(BaseModel):
    patient_code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = None
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    birth_date: Optional[str] = None
    notes: Optional[str] = None


class PatientResponse(BaseModel):
    id: int
    patient_code: str
    name: str
    gender: str
    birth_date: Optional[str]
    notes: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}
