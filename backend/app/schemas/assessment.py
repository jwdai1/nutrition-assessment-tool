"""Pydantic schemas for Assessment API."""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MNAInput(BaseModel):
    q_a: Optional[int] = Field(None, ge=0, le=2)
    q_b: Optional[int] = Field(None, ge=0, le=3)
    q_c: Optional[int] = Field(None, ge=0, le=2)
    q_d: Optional[int] = Field(None, ge=0, le=2)
    q_e: Optional[int] = Field(None, ge=0, le=2)
    q_f: Optional[int] = Field(None, ge=0, le=3)


class GLIMInput(BaseModel):
    weight_loss: int = Field(0, ge=0, le=1)
    low_bmi: int = Field(0, ge=0, le=1)
    muscle: str = Field("none", pattern="^(none|mild|severe)$")
    intake: int = Field(0, ge=0, le=1)
    inflam: int = Field(0, ge=0, le=1)
    chronic: int = Field(0, ge=0, le=1)


class AssessmentCreate(BaseModel):
    patient_id: int
    assess_date: str
    age_at_assess: int = Field(..., ge=0, le=150)
    height_cm: float = Field(..., gt=0)
    weight_kg: float = Field(..., gt=0)
    weight_3m_kg: Optional[float] = None
    weight_6m_kg: Optional[float] = None
    cc_cm: Optional[float] = None
    mna: MNAInput
    glim: GLIMInput


class IsocalRecommendation(BaseModel):
    show: bool
    product_name: str = ""
    description: str = ""
    permitted_claim: str = ""
    brand_url: str = ""
    purchase_url: str = ""


class AssessmentResponse(BaseModel):
    id: int
    patient_id: int
    assess_date: str
    age_at_assess: int
    height_cm: float
    weight_kg: float
    weight_3m_kg: Optional[float]
    weight_6m_kg: Optional[float]
    cc_cm: Optional[float]
    bmi: Optional[float]
    wl_pct_3m: Optional[float]
    wl_pct_6m: Optional[float]
    mna_q_a: Optional[int]
    mna_q_b: Optional[int]
    mna_q_c: Optional[int]
    mna_q_d: Optional[int]
    mna_q_e: Optional[int]
    mna_q_f: Optional[int]
    mna_total: Optional[int]
    mna_category: Optional[str]
    glim_weight_loss: int
    glim_low_bmi: int
    glim_muscle: str
    glim_intake: int
    glim_inflam: int
    glim_chronic: int
    glim_diagnosed: Optional[int]
    glim_severity: Optional[str]
    recommendations: List[str] = []
    reasons: List[str] = []
    isocal_recommendation: IsocalRecommendation
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ChartDataPoint(BaseModel):
    assess_date: str
    weight_kg: float
    bmi: Optional[float]
    mna_total: Optional[int]


class ChartResponse(BaseModel):
    data: List[ChartDataPoint]
