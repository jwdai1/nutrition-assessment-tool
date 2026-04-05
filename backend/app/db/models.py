"""SQLAlchemy ORM models — mirrors existing SQLite schema."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, Index,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class PatientModel(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, default="")
    gender = Column(String, nullable=False)
    birth_date = Column(String, nullable=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    assessments = relationship(
        "AssessmentModel", back_populates="patient", cascade="all, delete-orphan"
    )


class AssessmentModel(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    assess_date = Column(String, nullable=False)
    age_at_assess = Column(Integer, nullable=False)
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    weight_3m_kg = Column(Float, nullable=True)
    weight_6m_kg = Column(Float, nullable=True)
    cc_cm = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    wl_pct_3m = Column(Float, nullable=True)
    wl_pct_6m = Column(Float, nullable=True)
    mna_q_a = Column(Integer, nullable=True)
    mna_q_b = Column(Integer, nullable=True)
    mna_q_c = Column(Integer, nullable=True)
    mna_q_d = Column(Integer, nullable=True)
    mna_q_e = Column(Integer, nullable=True)
    mna_q_f = Column(Integer, nullable=True)
    mna_total = Column(Integer, nullable=True)
    mna_category = Column(String, nullable=True)
    glim_weight_loss = Column(Integer, default=0)
    glim_low_bmi = Column(Integer, default=0)
    glim_muscle = Column(String, default="none")
    glim_intake = Column(Integer, default=0)
    glim_inflam = Column(Integer, default=0)
    glim_chronic = Column(Integer, default=0)
    glim_diagnosed = Column(Integer, nullable=True)
    glim_severity = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    patient = relationship("PatientModel", back_populates="assessments")

    __table_args__ = (
        Index("idx_assessments_patient", "patient_id", "assess_date"),
    )
