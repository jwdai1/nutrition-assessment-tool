# Nutrition Assessment Web App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the PySide6 nutrition assessment desktop app to a Next.js + FastAPI web app with Isocal 100 product recommendation on GLIM malnutrition diagnosis.

**Architecture:** Next.js 14 (App Router) + Tailwind + shadcn/ui frontend communicating via REST API with a FastAPI backend. Existing Python diagnostic logic (`logic.py`) is ported directly. SQLite for dev, PostgreSQL-ready via SQLAlchemy + Alembic.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, WeasyPrint, openpyxl | Node 20+, Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, Recharts, React Hook Form, Zod, Vitest

---

## Phase 1: Backend Foundation

### Task 1: Project scaffolding and backend skeleton

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/requirements.txt`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/schemas/__init__.py`

- [ ] **Step 1: Create backend directory structure**

```bash
mkdir -p backend/app/{core,db,routers,schemas}
touch backend/app/__init__.py backend/app/core/__init__.py backend/app/db/__init__.py backend/app/routers/__init__.py backend/app/schemas/__init__.py
```

- [ ] **Step 2: Write requirements.txt**

Create `backend/requirements.txt`:

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.0
alembic>=1.13.0
pydantic>=2.0.0
weasyprint>=61.0
openpyxl>=3.1.0
python-multipart>=0.0.9
```

- [ ] **Step 3: Write config.py with Isocal product data**

Create `backend/app/config.py`:

```python
"""Application configuration and Isocal 100 product data."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./nutrition_tool.db"
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()

# Isocal 100 product recommendation (served from config so URL changes
# don't require a frontend redeploy)
ISOCAL_PRODUCT = {
    "product_name": "アイソカル® 100",
    "description": "100mlで200kcal、たんぱく質8g、ビタミン13種・ミネラル13種",
    "permitted_claim": (
        "本品は、食事として摂取すべき栄養素をバランスよく配合した総合栄養食品です。"
        "通常の食事で十分な栄養を摂ることができない方や低栄養の方の栄養補給に適しています。\n\n"
        "医師、管理栄養士等のご指導に従って使用してください。"
        "本品は栄養療法の素材として適するものであって、多く摂取することによって疾病が治癒するものではありません。"
    ),
    "brand_url": "https://healthscienceshop.nestle.jp/blogs/isocal/isocal-100-index",
    "purchase_url": "https://healthscienceshop.nestle.jp/products/isocal-100",
}
```

- [ ] **Step 4: Write main.py with CORS and health check**

Create `backend/app/main.py`:

```python
"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title="Nutrition Assessment Tool API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 5: Verify the server starts**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Visit http://localhost:8000/api/health → {"status": "ok"}
```

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat: scaffold FastAPI backend with config and health check"
```

---

### Task 2: Database layer (SQLAlchemy models + Alembic)

**Files:**
- Create: `backend/app/db/database.py`
- Create: `backend/app/db/models.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write the failing test for DB connection**

Create `backend/tests/__init__.py` and `backend/tests/conftest.py`:

```python
# backend/tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
```

Create `backend/tests/test_db.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_db.py::test_create_patient -v
# Expected: FAIL — ModuleNotFoundError: No module named 'app.db.database'
```

- [ ] **Step 3: Write database.py**

Create `backend/app/db/database.py`:

```python
"""SQLAlchemy engine, session, and Base."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: Write SQLAlchemy models**

Create `backend/app/db/models.py`:

```python
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
    gender = Column(String, nullable=False)  # 'male'|'female'|'other'
    birth_date = Column(String, nullable=True)  # YYYY-MM-DD
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

    # MNA-SF answers
    mna_q_a = Column(Integer, nullable=True)
    mna_q_b = Column(Integer, nullable=True)
    mna_q_c = Column(Integer, nullable=True)
    mna_q_d = Column(Integer, nullable=True)
    mna_q_e = Column(Integer, nullable=True)
    mna_q_f = Column(Integer, nullable=True)
    mna_total = Column(Integer, nullable=True)
    mna_category = Column(String, nullable=True)  # 'normal'|'risk'|'severe'

    # GLIM criteria
    glim_weight_loss = Column(Integer, default=0)
    glim_low_bmi = Column(Integer, default=0)
    glim_muscle = Column(String, default="none")  # 'none'|'mild'|'severe'
    glim_intake = Column(Integer, default=0)
    glim_inflam = Column(Integer, default=0)
    glim_chronic = Column(Integer, default=0)

    # GLIM result
    glim_diagnosed = Column(Integer, nullable=True)  # 0/1
    glim_severity = Column(String, nullable=True)  # null|'stage1'|'stage2'

    created_at = Column(DateTime, default=datetime.now)

    patient = relationship("PatientModel", back_populates="assessments")

    __table_args__ = (
        Index("idx_assessments_patient", "patient_id", "assess_date"),
    )
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend && python -m pytest tests/test_db.py::test_create_patient -v
# Expected: PASS
```

- [ ] **Step 6: Initialize Alembic**

```bash
cd backend && alembic init alembic
```

Edit `backend/alembic/env.py` — set `target_metadata`:

```python
# At the top, add:
from app.db.database import Base
from app.db.models import PatientModel, AssessmentModel  # noqa: F401

# Replace target_metadata = None with:
target_metadata = Base.metadata
```

Edit `backend/alembic.ini` — set `sqlalchemy.url`:

```
sqlalchemy.url = sqlite:///./nutrition_tool.db
```

```bash
cd backend && alembic revision --autogenerate -m "initial schema"
cd backend && alembic upgrade head
```

- [ ] **Step 7: Wire DB init into app startup**

Add to `backend/app/main.py`:

```python
from app.db.database import engine, Base
from app.db.models import PatientModel, AssessmentModel  # noqa: F401

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 8: Commit**

```bash
git add backend/
git commit -m "feat: add SQLAlchemy models, Alembic migrations, and DB tests"
```

---

### Task 3: Pydantic schemas

**Files:**
- Create: `backend/app/schemas/patient.py`
- Create: `backend/app/schemas/assessment.py`

- [ ] **Step 1: Write patient schemas**

Create `backend/app/schemas/patient.py`:

```python
"""Pydantic schemas for Patient API."""
from datetime import datetime
from typing import Optional
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
```

- [ ] **Step 2: Write assessment schemas**

Create `backend/app/schemas/assessment.py`:

```python
"""Pydantic schemas for Assessment API."""
from datetime import datetime
from typing import Optional
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

    recommendations: list[str] = []
    reasons: list[str] = []
    isocal_recommendation: IsocalRecommendation

    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ChartDataPoint(BaseModel):
    assess_date: str
    weight_kg: float
    bmi: Optional[float]
    mna_total: Optional[int]


class ChartResponse(BaseModel):
    data: list[ChartDataPoint]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: add Pydantic schemas for patient and assessment APIs"
```

---

### Task 4: Diagnostic logic (port from existing code)

**Files:**
- Create: `backend/app/core/logic.py`
- Create: `backend/app/core/recommendations.py`
- Create: `backend/tests/test_logic.py`

- [ ] **Step 1: Write tests for core logic**

Create `backend/tests/test_logic.py`:

```python
"""Tests for diagnostic logic — ported from existing logic.py."""
from app.core.logic import (
    calc_bmi,
    calc_weight_loss_pct,
    is_low_bmi_glim,
    is_low_bmi_severe,
    interpret_mna_sf_score,
    interpret_weight_loss_glim,
    calc_glim_severity,
    auto_estimate_mna_q_b,
    auto_estimate_mna_q_f_bmi,
    auto_estimate_mna_q_f_cc,
)
from app.core.recommendations import get_recommendations, should_show_isocal


# --- BMI ---
def test_calc_bmi_normal():
    assert round(calc_bmi(60.0, 165.0), 1) == 22.0

def test_calc_bmi_none_weight():
    assert calc_bmi(None, 165.0) is None

def test_calc_bmi_zero_height():
    assert calc_bmi(60.0, 0) is None


# --- Weight loss ---
def test_weight_loss_pct():
    assert round(calc_weight_loss_pct(54.0, 60.0), 1) == 10.0

def test_weight_loss_pct_none():
    assert calc_weight_loss_pct(None, 60.0) is None


# --- GLIM BMI ---
def test_low_bmi_glim_elderly():
    assert is_low_bmi_glim(21.5, 75) is True   # <22 for ≥70
    assert is_low_bmi_glim(22.5, 75) is False

def test_low_bmi_glim_young():
    assert is_low_bmi_glim(19.5, 60) is True    # <20 for <70
    assert is_low_bmi_glim(20.5, 60) is False

def test_low_bmi_severe_elderly():
    assert is_low_bmi_severe(19.5, 75) is True   # <20 for ≥70
    assert is_low_bmi_severe(20.5, 75) is False

def test_low_bmi_severe_young():
    assert is_low_bmi_severe(18.0, 60) is True    # <18.5 for <70
    assert is_low_bmi_severe(19.0, 60) is False


# --- MNA-SF ---
def test_mna_normal():
    result = interpret_mna_sf_score(13)
    assert result["category"] == "normal"

def test_mna_risk():
    result = interpret_mna_sf_score(10)
    assert result["category"] == "risk"

def test_mna_severe():
    result = interpret_mna_sf_score(5)
    assert result["category"] == "severe"

def test_mna_none():
    result = interpret_mna_sf_score(None)
    assert result["category"] == "unknown"


# --- MNA auto-estimate ---
def test_auto_q_b_big_loss():
    assert auto_estimate_mna_q_b(57.0, 61.0) == 0  # 4kg loss ≥ 3

def test_auto_q_b_small_loss():
    assert auto_estimate_mna_q_b(59.0, 61.0) == 2  # 2kg loss

def test_auto_q_b_no_loss():
    assert auto_estimate_mna_q_b(61.0, 60.0) == 3  # gained

def test_auto_q_f_bmi_low():
    assert auto_estimate_mna_q_f_bmi(18.0) == 0

def test_auto_q_f_bmi_high():
    assert auto_estimate_mna_q_f_bmi(24.0) == 3

def test_auto_q_f_cc_low():
    assert auto_estimate_mna_q_f_cc(29.0) == 0

def test_auto_q_f_cc_high():
    assert auto_estimate_mna_q_f_cc(32.0) == 3


# --- GLIM weight loss interpretation ---
def test_weight_loss_glim_moderate_3m():
    result = interpret_weight_loss_glim(7.0, None)
    assert result["present"] is True
    assert result["severe"] is False

def test_weight_loss_glim_severe_3m():
    result = interpret_weight_loss_glim(12.0, None)
    assert result["present"] is True
    assert result["severe"] is True


# --- GLIM severity ---
def test_glim_diagnosed_stage1():
    result = calc_glim_severity(
        glim_weight_loss=True, glim_low_bmi=False, glim_muscle="none",
        glim_intake=True, glim_inflam=False, glim_chronic=False,
        age=75, bmi=22.5, wl_pct_3m=7.0, wl_pct_6m=None,
    )
    assert result["diagnosed"] is True
    assert result["severity"] == "stage1"

def test_glim_diagnosed_stage2():
    result = calc_glim_severity(
        glim_weight_loss=True, glim_low_bmi=True, glim_muscle="severe",
        glim_intake=True, glim_inflam=True, glim_chronic=False,
        age=75, bmi=18.0, wl_pct_3m=15.0, wl_pct_6m=None,
    )
    assert result["diagnosed"] is True
    assert result["severity"] == "stage2"

def test_glim_not_diagnosed():
    result = calc_glim_severity(
        glim_weight_loss=True, glim_low_bmi=False, glim_muscle="none",
        glim_intake=False, glim_inflam=False, glim_chronic=False,
        age=60, bmi=21.0, wl_pct_3m=7.0, wl_pct_6m=None,
    )
    assert result["diagnosed"] is False


# --- Recommendations ---
def test_recommendations_normal():
    recs = get_recommendations("normal", False, None)
    assert len(recs) == 1
    assert "定期的" in recs[0]

def test_recommendations_stage2():
    recs = get_recommendations("severe", True, "stage2")
    assert any("Stage 2" in r for r in recs)


# --- Isocal ---
def test_isocal_show_when_diagnosed():
    assert should_show_isocal(True) is True

def test_isocal_hide_when_not_diagnosed():
    assert should_show_isocal(False) is False

def test_isocal_hide_when_none():
    assert should_show_isocal(None) is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_logic.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Port logic.py**

Create `backend/app/core/logic.py` — direct copy from existing `logic.py` with import path fix:

```python
"""Pure diagnostic functions — ported from PySide6 version."""
from __future__ import annotations
from typing import Optional


def calc_bmi(weight: Optional[float], height: Optional[float]) -> Optional[float]:
    if not weight or not height or height <= 0:
        return None
    return weight / ((height / 100) ** 2)


def calc_weight_loss_pct(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    if not current or not previous or previous <= 0:
        return None
    return ((previous - current) / previous) * 100


def is_low_bmi_glim(bmi: Optional[float], age: int) -> bool:
    if bmi is None:
        return False
    return bmi < 22 if age >= 70 else bmi < 20


def is_low_bmi_severe(bmi: Optional[float], age: int) -> bool:
    if bmi is None:
        return False
    return bmi < 20 if age >= 70 else bmi < 18.5


def interpret_mna_sf_score(total: Optional[int]) -> dict:
    if total is None:
        return {"category": "unknown", "label": "未入力", "color_key": "muted"}
    if total >= 12:
        return {"category": "normal", "label": "栄養良好", "color_key": "normal"}
    if total >= 8:
        return {"category": "risk", "label": "低栄養のリスクあり", "color_key": "risk"}
    return {"category": "severe", "label": "低栄養の可能性", "color_key": "mal"}


def interpret_weight_loss_glim(
    pct_3m: Optional[float],
    pct_6m: Optional[float],
) -> dict:
    present = False
    severe = False
    detail = ""

    if pct_3m is not None and pct_3m > 5:
        present = True
        if pct_3m > 10:
            severe = True
            detail = f"3ヶ月体重減少率 {pct_3m:.1f}%（高度: >10%）"
        else:
            detail = f"3ヶ月体重減少率 {pct_3m:.1f}%（中等度: >5%）"

    if pct_6m is not None and pct_6m > 10:
        present = True
        if pct_6m > 20:
            severe = True
            suffix = f"6ヶ月体重減少率 {pct_6m:.1f}%（高度: >20%）"
        else:
            suffix = f"6ヶ月体重減少率 {pct_6m:.1f}%（中等度: >10%）"
        detail = (detail + " / " + suffix) if detail else suffix

    if not present and (pct_3m is not None or pct_6m is not None):
        detail = "体重減少なし（基準未満）"

    if pct_3m is None and pct_6m is None:
        detail = "体重データなし（手動確認が必要）"

    return {"present": present, "severe": severe, "detail": detail}


def calc_glim_severity(
    glim_weight_loss: bool,
    glim_low_bmi: bool,
    glim_muscle: str,
    glim_intake: bool,
    glim_inflam: bool,
    glim_chronic: bool,
    age: int,
    bmi: Optional[float],
    wl_pct_3m: Optional[float],
    wl_pct_6m: Optional[float],
) -> dict:
    phenotypic_met = glim_weight_loss or glim_low_bmi or glim_muscle != "none"
    etiologic_met = glim_intake or glim_inflam or glim_chronic
    diagnosed = phenotypic_met and etiologic_met

    phenotypic_items: list[str] = []
    etiologic_items: list[str] = []
    reasons: list[str] = []

    if glim_weight_loss:
        phenotypic_items.append("体重減少")
    if glim_low_bmi:
        phenotypic_items.append("低BMI")
    if glim_muscle == "mild":
        phenotypic_items.append("筋肉量低下（軽〜中等度）")
    elif glim_muscle == "severe":
        phenotypic_items.append("筋肉量低下（高度）")

    if glim_intake:
        etiologic_items.append("食事摂取量低下 / 消化吸収障害")
    if glim_inflam:
        etiologic_items.append("急性疾患・外傷による炎症")
    if glim_chronic:
        etiologic_items.append("慢性疾患による炎症")

    if not diagnosed:
        return {
            "diagnosed": False,
            "severity": None,
            "reasons": reasons,
            "phenotypic_met": phenotypic_met,
            "etiologic_met": etiologic_met,
            "phenotypic_items": phenotypic_items,
            "etiologic_items": etiologic_items,
        }

    stage2 = False

    if glim_weight_loss:
        wl3_severe = wl_pct_3m is not None and wl_pct_3m > 10
        wl6_severe = wl_pct_6m is not None and wl_pct_6m > 20
        if wl3_severe or wl6_severe:
            stage2 = True
            if wl3_severe:
                reasons.append(f"3ヶ月体重減少率 {wl_pct_3m:.1f}%（Stage 2基準: >10%）")
            if wl6_severe:
                reasons.append(f"6ヶ月体重減少率 {wl_pct_6m:.1f}%（Stage 2基準: >20%）")
        else:
            if wl_pct_3m is not None and wl_pct_3m > 5:
                reasons.append(f"3ヶ月体重減少率 {wl_pct_3m:.1f}%（Stage 1基準: 5〜10%）")
            if wl_pct_6m is not None and wl_pct_6m > 10:
                reasons.append(f"6ヶ月体重減少率 {wl_pct_6m:.1f}%（Stage 1基準: 10〜20%）")
            if wl_pct_3m is None and wl_pct_6m is None:
                reasons.append("意図しない体重減少あり（臨床判断）")

    if glim_low_bmi and bmi is not None:
        if is_low_bmi_severe(bmi, age):
            stage2 = True
            reasons.append(f"BMI {bmi:.1f} — 高度低BMI（Stage 2: 70歳未満<18.5 / 70歳以上<20）")
        else:
            reasons.append(f"BMI {bmi:.1f} — 低BMI（Stage 1: 70歳未満<20 / 70歳以上<22）")
    elif glim_low_bmi:
        reasons.append("低BMIあり（臨床判断、BMI計算不可）")

    if glim_muscle == "severe":
        stage2 = True
        reasons.append("筋肉量の高度低下（Stage 2基準）")
    elif glim_muscle == "mild":
        reasons.append("筋肉量の軽〜中等度低下（Stage 1基準）")

    if glim_intake:
        reasons.append("食事摂取量の低下 / 消化吸収障害あり")
    if glim_inflam:
        reasons.append("急性疾患・外傷による炎症あり")
    if glim_chronic:
        reasons.append("慢性疾患による中等度炎症あり")

    return {
        "diagnosed": True,
        "severity": "stage2" if stage2 else "stage1",
        "reasons": reasons,
        "phenotypic_met": phenotypic_met,
        "etiologic_met": etiologic_met,
        "phenotypic_items": phenotypic_items,
        "etiologic_items": etiologic_items,
    }


def auto_estimate_mna_q_b(
    weight_kg: Optional[float],
    weight_3m_kg: Optional[float],
) -> Optional[int]:
    if weight_kg is None or weight_3m_kg is None:
        return None
    loss = weight_3m_kg - weight_kg
    if loss >= 3:
        return 0
    if loss > 0:
        return 2
    return 3


def auto_estimate_mna_q_f_bmi(bmi: Optional[float]) -> Optional[int]:
    if bmi is None:
        return None
    if bmi < 19:
        return 0
    if bmi < 21:
        return 1
    if bmi < 23:
        return 2
    return 3


def auto_estimate_mna_q_f_cc(cc_cm: Optional[float]) -> Optional[int]:
    if cc_cm is None:
        return None
    return 3 if cc_cm >= 31 else 0
```

- [ ] **Step 4: Write recommendations.py**

Create `backend/app/core/recommendations.py`:

```python
"""Recommendation logic and Isocal 100 display decision."""
from __future__ import annotations
from typing import Optional


def get_recommendations(
    mna_category: Optional[str],
    glim_diagnosed: Optional[bool],
    glim_severity: Optional[str],
) -> list[str]:
    if mna_category == "normal":
        return ["定期的な栄養スクリーニング（6ヶ月毎）を継続してください。"]
    if not glim_diagnosed:
        return [
            "低栄養リスクとして栄養ケアプランの検討を行い、1〜3ヶ月後に再評価してください。",
            "管理栄養士への相談・連携を推奨します。",
        ]
    if glim_severity == "stage2":
        return [
            "高度低栄養（Stage 2）：速やかに栄養介入を開始し、多職種チームによる栄養管理を実施してください。",
            "入院または専門施設での集中的な栄養サポートを検討してください。",
            "1ヶ月以内に再評価を実施してください。",
        ]
    return [
        "中等度低栄養（Stage 1）：管理栄養士による栄養介入計画を策定してください。",
        "2〜4週間後に栄養摂取状況を確認し、1〜2ヶ月後に再評価してください。",
    ]


def should_show_isocal(glim_diagnosed: Optional[bool]) -> bool:
    return glim_diagnosed is True
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_logic.py -v
# Expected: all PASS
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/ backend/tests/test_logic.py
git commit -m "feat: port diagnostic logic and add Isocal recommendation function"
```

---

### Task 5: CRUD operations

**Files:**
- Create: `backend/app/db/crud.py`
- Create: `backend/tests/test_crud.py`

- [ ] **Step 1: Write CRUD tests**

Create `backend/tests/test_crud.py`:

```python
"""Tests for CRUD operations."""
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
    assert results[0].name == "田中太郎"

    results = search_patients(db, "PT-000")
    assert len(results) == 2


def test_update_patient(db):
    patient = create_patient(db, PatientCreate(patient_code="PT-0001", name="旧名", gender="male"))
    updated = update_patient(db, patient.id, PatientUpdate(name="新名"))
    assert updated.name == "新名"
    assert updated.patient_code == "PT-0001"


def test_delete_patient(db):
    patient = create_patient(db, PatientCreate(patient_code="PT-0001", name="削除テスト", gender="male"))
    delete_patient(db, patient.id)
    assert get_patient(db, patient.id) is None


def test_patient_code_exists(db):
    create_patient(db, PatientCreate(patient_code="PT-0001", name="テスト", gender="male"))
    assert patient_code_exists(db, "PT-0001") is True
    assert patient_code_exists(db, "PT-9999") is False


def test_create_and_get_assessment(db):
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

    fetched = get_assessment(db, assessment.id)
    assert fetched.patient_id == patient.id


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
    assert assessments[0].assess_date == "2026-03-01"  # DESC order
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_crud.py -v
# Expected: FAIL — ImportError
```

- [ ] **Step 3: Write crud.py**

Create `backend/app/db/crud.py`:

```python
"""CRUD operations for patients and assessments."""
from __future__ import annotations
from typing import Optional

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


def get_all_patients(db: Session) -> list[PatientModel]:
    return db.query(PatientModel).order_by(PatientModel.updated_at.desc()).all()


def search_patients(db: Session, query: str) -> list[PatientModel]:
    like = f"%{query}%"
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

    # Compute derived values
    bmi = logic.calc_bmi(data.weight_kg, data.height_cm)
    wl_pct_3m = logic.calc_weight_loss_pct(data.weight_kg, data.weight_3m_kg)
    wl_pct_6m = logic.calc_weight_loss_pct(data.weight_kg, data.weight_6m_kg)

    mna_answers = [mna.q_a, mna.q_b, mna.q_c, mna.q_d, mna.q_e, mna.q_f]
    mna_total = sum(a for a in mna_answers if a is not None) if all(a is not None for a in mna_answers) else None
    mna_interp = logic.interpret_mna_sf_score(mna_total)
    mna_category = mna_interp["category"] if mna_interp["category"] != "unknown" else None

    # GLIM — only if MNA < 12
    glim_diagnosed = None
    glim_severity = None
    if mna_total is not None and mna_total < 12:
        glim_wl = bool(glim.weight_loss)
        glim_low = bool(glim.low_bmi)
        glim_result = logic.calc_glim_severity(
            glim_weight_loss=glim_wl,
            glim_low_bmi=glim_low,
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


def get_assessments_for_patient(db: Session, patient_id: int) -> list[AssessmentModel]:
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_crud.py -v
# Expected: all PASS
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/db/crud.py backend/tests/test_crud.py
git commit -m "feat: add CRUD operations with diagnostic logic integration"
```

---

### Task 6: API routers (patients + assessments)

**Files:**
- Create: `backend/app/routers/patients.py`
- Create: `backend/app/routers/assessments.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_api_patients.py`
- Create: `backend/tests/test_api_assessments.py`

- [ ] **Step 1: Write patient API tests**

Create `backend/tests/test_api_patients.py`:

```python
"""Tests for patient API endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, get_db

from tests.conftest import engine, TestingSessionLocal


@pytest.fixture(autouse=True)
def setup():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_patient(client):
    resp = client.post("/api/patients", json={
        "patient_code": "PT-0001", "name": "田中太郎", "gender": "male"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["patient_code"] == "PT-0001"
    assert data["id"] is not None


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


def test_get_patient(client):
    create_resp = client.post("/api/patients", json={"patient_code": "PT-0001", "name": "テスト", "gender": "male"})
    pid = create_resp.json()["id"]
    resp = client.get(f"/api/patients/{pid}")
    assert resp.status_code == 200
    assert resp.json()["patient_code"] == "PT-0001"


def test_update_patient(client):
    create_resp = client.post("/api/patients", json={"patient_code": "PT-0001", "name": "旧名", "gender": "male"})
    pid = create_resp.json()["id"]
    resp = client.put(f"/api/patients/{pid}", json={"name": "新名"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "新名"


def test_delete_patient(client):
    create_resp = client.post("/api/patients", json={"patient_code": "PT-0001", "name": "テスト", "gender": "male"})
    pid = create_resp.json()["id"]
    resp = client.delete(f"/api/patients/{pid}")
    assert resp.status_code == 204
    resp = client.get(f"/api/patients/{pid}")
    assert resp.status_code == 404


def test_duplicate_patient_code(client):
    client.post("/api/patients", json={"patient_code": "PT-0001", "name": "A", "gender": "male"})
    resp = client.post("/api/patients", json={"patient_code": "PT-0001", "name": "B", "gender": "female"})
    assert resp.status_code == 409
```

- [ ] **Step 2: Write patients router**

Create `backend/app/routers/patients.py`:

```python
"""Patient CRUD API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.db import crud
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("", response_model=list[PatientResponse])
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
```

- [ ] **Step 3: Write assessment API tests**

Create `backend/tests/test_api_assessments.py`:

```python
"""Tests for assessment API endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, get_db
from tests.conftest import engine, TestingSessionLocal


@pytest.fixture(autouse=True)
def setup():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def patient_id(client):
    resp = client.post("/api/patients", json={
        "patient_code": "PT-0001", "name": "テスト", "gender": "male"
    })
    return resp.json()["id"]


def _assessment_payload(patient_id, mna_total_target="low"):
    """Helper to build assessment payload."""
    if mna_total_target == "low":
        mna = {"q_a": 0, "q_b": 0, "q_c": 1, "q_d": 0, "q_e": 1, "q_f": 0}
    else:
        mna = {"q_a": 2, "q_b": 3, "q_c": 2, "q_d": 2, "q_e": 2, "q_f": 3}
    return {
        "patient_id": patient_id,
        "assess_date": "2026-04-06",
        "age_at_assess": 75,
        "height_cm": 160.0,
        "weight_kg": 50.0,
        "weight_3m_kg": 55.0,
        "mna": mna,
        "glim": {"weight_loss": 1, "intake": 1},
    }


def test_create_assessment_with_glim_diagnosis(client, patient_id):
    resp = client.post("/api/assessments", json=_assessment_payload(patient_id, "low"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["glim_diagnosed"] == 1
    assert data["isocal_recommendation"]["show"] is True
    assert "アイソカル" in data["isocal_recommendation"]["product_name"]


def test_create_assessment_normal(client, patient_id):
    resp = client.post("/api/assessments", json=_assessment_payload(patient_id, "high"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["mna_category"] == "normal"
    assert data["isocal_recommendation"]["show"] is False


def test_get_assessment(client, patient_id):
    create_resp = client.post("/api/assessments", json=_assessment_payload(patient_id))
    aid = create_resp.json()["id"]
    resp = client.get(f"/api/assessments/{aid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == aid


def test_get_assessments_for_patient(client, patient_id):
    client.post("/api/assessments", json=_assessment_payload(patient_id))
    resp = client.get(f"/api/patients/{patient_id}/assessments")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_chart_data(client, patient_id):
    client.post("/api/assessments", json=_assessment_payload(patient_id))
    resp = client.get(f"/api/patients/{patient_id}/assessments/chart")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert "weight_kg" in data[0]
    assert "bmi" in data[0]
```

- [ ] **Step 4: Write assessments router**

Create `backend/app/routers/assessments.py`:

```python
"""Assessment API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.schemas.assessment import (
    AssessmentCreate, AssessmentResponse, IsocalRecommendation,
    ChartResponse, ChartDataPoint,
)
from app.core.logic import interpret_mna_sf_score, calc_glim_severity
from app.core.recommendations import get_recommendations, should_show_isocal
from app.config import ISOCAL_PRODUCT

router = APIRouter(tags=["assessments"])


def _build_response(assessment) -> dict:
    """Build full assessment response with recommendations and Isocal."""
    a = assessment
    mna_interp = interpret_mna_sf_score(a.mna_total)

    reasons = []
    if a.glim_diagnosed and a.mna_total is not None and a.mna_total < 12:
        glim_result = calc_glim_severity(
            glim_weight_loss=bool(a.glim_weight_loss),
            glim_low_bmi=bool(a.glim_low_bmi),
            glim_muscle=a.glim_muscle or "none",
            glim_intake=bool(a.glim_intake),
            glim_inflam=bool(a.glim_inflam),
            glim_chronic=bool(a.glim_chronic),
            age=a.age_at_assess,
            bmi=a.bmi,
            wl_pct_3m=a.wl_pct_3m,
            wl_pct_6m=a.wl_pct_6m,
        )
        reasons = glim_result.get("reasons", [])

    recs = get_recommendations(
        a.mna_category,
        bool(a.glim_diagnosed) if a.glim_diagnosed is not None else None,
        a.glim_severity,
    )

    show_isocal = should_show_isocal(
        bool(a.glim_diagnosed) if a.glim_diagnosed is not None else None
    )

    isocal = IsocalRecommendation(
        show=show_isocal,
        **(ISOCAL_PRODUCT if show_isocal else {}),
    )

    return {
        **{c.name: getattr(a, c.name) for c in a.__table__.columns},
        "recommendations": recs,
        "reasons": reasons,
        "isocal_recommendation": isocal,
    }


@router.post("/api/assessments", response_model=AssessmentResponse, status_code=201)
def create_assessment(data: AssessmentCreate, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, data.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    assessment = crud.create_assessment(db, data)
    return _build_response(assessment)


@router.get("/api/assessments/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    assessment = crud.get_assessment(db, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return _build_response(assessment)


@router.get("/api/patients/{patient_id}/assessments", response_model=list[AssessmentResponse])
def list_assessments(patient_id: int, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    assessments = crud.get_assessments_for_patient(db, patient_id)
    return [_build_response(a) for a in assessments]


@router.get("/api/patients/{patient_id}/assessments/chart", response_model=ChartResponse)
def chart_data(patient_id: int, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    assessments = crud.get_assessments_for_patient(db, patient_id)
    data = [
        ChartDataPoint(
            assess_date=a.assess_date,
            weight_kg=a.weight_kg,
            bmi=a.bmi,
            mna_total=a.mna_total,
        )
        for a in reversed(assessments)  # chronological order for chart
    ]
    return ChartResponse(data=data)
```

- [ ] **Step 5: Register routers in main.py**

Add to `backend/app/main.py`:

```python
from app.routers import patients, assessments

app.include_router(patients.router)
app.include_router(assessments.router)
```

- [ ] **Step 6: Run all tests**

```bash
cd backend && python -m pytest -v
# Expected: all PASS
```

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat: add patient and assessment API routers with full test coverage"
```

---

### Task 7: Export routers (CSV, Excel, PDF)

**Files:**
- Create: `backend/app/routers/export.py`
- Create: `backend/app/routers/pdf.py`
- Create: `backend/tests/test_api_export.py`

- [ ] **Step 1: Write export tests**

Create `backend/tests/test_api_export.py`:

```python
"""Tests for CSV, Excel, and PDF export endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, get_db
from tests.conftest import engine, TestingSessionLocal


@pytest.fixture(autouse=True)
def setup():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def assessment_id(client):
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
    return resp.json()["id"], pid


def test_csv_export(client, assessment_id):
    _, pid = assessment_id
    resp = client.get(f"/api/export/patients/{pid}/csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/csv; charset=utf-8"
    assert "PT-0001" in resp.text


def test_excel_export(client, assessment_id):
    _, pid = assessment_id
    resp = client.get(f"/api/export/patients/{pid}/excel")
    assert resp.status_code == 200
    assert "spreadsheet" in resp.headers["content-type"]


def test_pdf_export(client, assessment_id):
    aid, _ = assessment_id
    resp = client.get(f"/api/assessments/{aid}/pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_api_export.py -v
# Expected: FAIL — 404 (routes don't exist yet)
```

- [ ] **Step 3: Write export router (CSV + Excel)**

Create `backend/app/routers/export.py`:

```python
"""CSV and Excel export endpoints."""
import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud

router = APIRouter(prefix="/api/export", tags=["export"])

CSV_COLUMNS = [
    ("assess_date", "評価日"),
    ("age_at_assess", "年齢"),
    ("height_cm", "身長(cm)"),
    ("weight_kg", "体重(kg)"),
    ("bmi", "BMI"),
    ("wl_pct_3m", "体重減少率3M(%)"),
    ("wl_pct_6m", "体重減少率6M(%)"),
    ("mna_total", "MNA-SF合計"),
    ("mna_category", "MNA判定"),
    ("glim_diagnosed", "GLIM診断"),
    ("glim_severity", "GLIM重症度"),
]


@router.get("/patients/{patient_id}/csv")
def export_csv(patient_id: int, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    assessments = crud.get_assessments_for_patient(db, patient_id)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([col[1] for col in CSV_COLUMNS])
    for a in assessments:
        writer.writerow([getattr(a, col[0]) for col in CSV_COLUMNS])

    buf.seek(0)
    filename = f"assessments_{patient.patient_code}.csv"
    return StreamingResponse(
        buf,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/patients/{patient_id}/excel")
def export_excel(patient_id: int, db: Session = Depends(get_db)):
    from openpyxl import Workbook

    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    assessments = crud.get_assessments_for_patient(db, patient_id)

    wb = Workbook()
    ws = wb.active
    ws.title = "評価履歴"
    ws.append([col[1] for col in CSV_COLUMNS])
    for a in assessments:
        ws.append([getattr(a, col[0]) for col in CSV_COLUMNS])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"assessments_{patient.patient_code}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

- [ ] **Step 4: Write PDF router**

Create `backend/app/routers/pdf.py`:

```python
"""PDF export endpoint using WeasyPrint."""
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.core.logic import interpret_mna_sf_score, calc_glim_severity
from app.core.recommendations import get_recommendations

router = APIRouter(tags=["pdf"])

PDF_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: "Hiragino Sans", "Yu Gothic", sans-serif; font-size: 11px; color: #111827; margin: 20mm; }}
  h1 {{ color: #1a56a4; font-size: 16px; border-bottom: 2px solid #1a56a4; padding-bottom: 4px; }}
  h2 {{ color: #1a56a4; font-size: 13px; margin-top: 16px; border-bottom: 1px solid #d1d5db; padding-bottom: 2px; }}
  .banner {{ padding: 10px 14px; border-radius: 6px; font-weight: bold; font-size: 13px; margin: 12px 0; }}
  .banner-normal {{ background: #e6f5ec; border: 2px solid #1a7a4a; color: #1a7a4a; }}
  .banner-risk {{ background: #fef3c7; border: 2px solid #b45309; color: #b45309; }}
  .banner-mal {{ background: #fdecea; border: 2px solid #c0392b; color: #c0392b; }}
  table {{ width: 100%; border-collapse: collapse; margin: 8px 0; }}
  td {{ padding: 3px 8px; }}
  td.label {{ color: #6b7280; width: 35%; }}
  td.value {{ font-weight: bold; }}
  .rec {{ background: #fef3c7; border: 1px solid #fcd34d; border-radius: 4px; padding: 6px 10px; margin: 4px 0; }}
  .rec-severe {{ background: #fdecea; border-color: #fca5a5; }}
  .footer {{ margin-top: 20px; padding-top: 8px; border-top: 1px solid #d1d5db; font-size: 9px; color: #6b7280; }}
</style>
</head>
<body>
<h1>低栄養診断レポート（MNA-SF / GLIM）</h1>

<h2>患者情報</h2>
<table>
  <tr><td class="label">患者ID</td><td class="value">{patient_code}</td></tr>
  <tr><td class="label">氏名</td><td class="value">{name}</td></tr>
  <tr><td class="label">評価日</td><td class="value">{assess_date}</td></tr>
  <tr><td class="label">性別 / 年齢</td><td class="value">{gender_label} / {age}歳</td></tr>
  <tr><td class="label">身長 / 体重</td><td class="value">{height}cm / {weight}kg</td></tr>
  <tr><td class="label">BMI</td><td class="value">{bmi}</td></tr>
</table>

<div class="banner {banner_class}">{banner_text}</div>

<h2>MNA-SF スコア</h2>
<p><strong>{mna_total} / 14点 — {mna_label}</strong></p>

{glim_section}

<h2>推奨アクション</h2>
{recommendations_html}

<div class="footer">
このツールは臨床判断を支援するためのものです。MNA&reg; は Nestl&eacute; の登録商標です。GLIM基準: Cederholm T, et al. JPEN 2019.
</div>
</body>
</html>"""


@router.get("/api/assessments/{assessment_id}/pdf")
def export_pdf(assessment_id: int, db: Session = Depends(get_db)):
    from weasyprint import HTML

    a = crud.get_assessment(db, assessment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    patient = crud.get_patient(db, a.patient_id)

    mna_interp = interpret_mna_sf_score(a.mna_total)
    skip_glim = a.mna_total is not None and a.mna_total >= 12

    # Banner
    if skip_glim:
        banner_class, banner_text = "banner-normal", "栄養良好（MNA-SF ≥12）"
    elif not a.glim_diagnosed:
        banner_class, banner_text = "banner-risk", "低栄養非該当（要観察）"
    else:
        sev = a.glim_severity
        banner_class = "banner-mal"
        banner_text = "低栄養（Stage 2: 高度）" if sev == "stage2" else "低栄養（Stage 1: 中等度）"

    # GLIM section
    glim_section = ""
    if not skip_glim and a.glim_diagnosed:
        glim_result = calc_glim_severity(
            bool(a.glim_weight_loss), bool(a.glim_low_bmi), a.glim_muscle or "none",
            bool(a.glim_intake), bool(a.glim_inflam), bool(a.glim_chronic),
            a.age_at_assess, a.bmi, a.wl_pct_3m, a.wl_pct_6m,
        )
        reasons_html = "".join(f"<li>{r}</li>" for r in glim_result.get("reasons", []))
        glim_section = f"<h2>GLIM 評価結果</h2><ul>{reasons_html}</ul>"

    # Recommendations
    recs = get_recommendations(
        a.mna_category,
        bool(a.glim_diagnosed) if a.glim_diagnosed is not None else None,
        a.glim_severity,
    )
    rec_class = "rec-severe" if a.glim_severity == "stage2" else "rec"
    recommendations_html = "".join(f'<div class="{rec_class}">{r}</div>' for r in recs)

    gender_map = {"male": "男性", "female": "女性", "other": "その他"}
    html_str = PDF_HTML_TEMPLATE.format(
        patient_code=patient.patient_code,
        name=patient.name or "—",
        assess_date=a.assess_date,
        gender_label=gender_map.get(patient.gender, patient.gender),
        age=a.age_at_assess,
        height=f"{a.height_cm:.1f}",
        weight=f"{a.weight_kg:.1f}",
        bmi=f"{a.bmi:.1f}" if a.bmi else "—",
        banner_class=banner_class,
        banner_text=banner_text,
        mna_total=a.mna_total if a.mna_total is not None else "—",
        mna_label=mna_interp.get("label", ""),
        glim_section=glim_section,
        recommendations_html=recommendations_html,
    )

    pdf_bytes = HTML(string=html_str).write_pdf()
    buf = io.BytesIO(pdf_bytes)

    filename = f"report_{patient.patient_code}_{a.assess_date}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

- [ ] **Step 5: Register export routers in main.py**

Add to `backend/app/main.py`:

```python
from app.routers import patients, assessments, export, pdf

app.include_router(patients.router)
app.include_router(assessments.router)
app.include_router(export.router)
app.include_router(pdf.router)
```

- [ ] **Step 6: Run all tests**

```bash
cd backend && python -m pytest -v
# Expected: all PASS
```

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat: add CSV, Excel, and PDF export endpoints"
```

---

## Phase 2: Figma Design

### Task 8: Create Figma UI designs for all 7 screens

**This task uses the Figma MCP tools.** Create designs for all screens defined in the spec.

- [ ] **Step 1: Design the patient list screen**

Using Figma MCP `create_new_file`, create a new Figma file named "Nutrition Assessment Tool — Web UI". Design the patient list page (`/patients`) with:
- Clean header with app title "低栄養診断ツール"
- Search bar at top
- Patient table/cards with columns: 患者ID, 氏名, 性別, 最終評価日
- Floating "＋ 患者追加" button
- Color palette: primary #1a56a4, normal #1a7a4a, risk #b45309, mal #c0392b, bg #f3f4f6

- [ ] **Step 2: Design the patient detail screen**

Design `/patients/[id]` with:
- Patient info card (code, name, gender, DOB, notes)
- Edit/Delete buttons
- Assessment history table (date, MNA score, GLIM result, severity)
- Recharts-style line chart placeholder (weight, BMI, MNA over time)
- "新規評価" CTA button

- [ ] **Step 3: Design the assessment wizard (Steps 1-3)**

Design the stepper wizard with:
- Progress indicator (Step 1/4, 2/4, 3/4, 4/4)
- Step 1: Form fields for date, age, height, weight, past weights, CC
- Step 2: MNA-SF radio groups (Q-A through Q-F) with score bar
- Step 3: GLIM criteria checkboxes and combo (conditionally shown when MNA < 12)
- Back/Next navigation buttons

- [ ] **Step 4: Design the result screen with Isocal banner**

Design `/assess/[id]` with:
- Diagnosis banner (green/yellow/red based on result)
- Score summary card
- GLIM breakdown (phenotypic + etiologic criteria)
- Recommendation action cards
- **Isocal 100 recommendation banner** (only shown for GLIM-diagnosed):
  - Product image placeholder
  - Product name "アイソカル® 100"
  - Key specs "100mlで200kcal、たんぱく質8g"
  - Full permitted claim text (both paragraphs)
  - Two CTA buttons: "製品について詳しく" / "ご購入はこちら"
- PDF export button, Back to patient button

- [ ] **Step 5: Get screenshot of all designs**

Use `get_screenshot` to capture each frame and verify the design quality.

- [ ] **Step 6: Commit any design-related config or assets**

```bash
git commit -m "docs: add Figma design references for all screens"
```

---

## Phase 3: Frontend Implementation

### Task 9: Next.js project scaffolding

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/lib/api.ts`

- [ ] **Step 1: Initialize Next.js project**

```bash
cd /path/to/project
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*"
```

- [ ] **Step 2: Install dependencies**

```bash
cd frontend
npm install recharts react-hook-form @hookform/resolvers zod
npx shadcn@latest init -d
npx shadcn@latest add button card dialog form input label select table tabs badge separator sheet toast
```

- [ ] **Step 3: Write API client**

Create `frontend/lib/api.ts`:

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// --- Types ---
export interface Patient {
  id: number;
  patient_code: string;
  name: string;
  gender: string;
  birth_date: string | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface IsocalRecommendation {
  show: boolean;
  product_name: string;
  description: string;
  permitted_claim: string;
  brand_url: string;
  purchase_url: string;
}

export interface Assessment {
  id: number;
  patient_id: number;
  assess_date: string;
  age_at_assess: number;
  height_cm: number;
  weight_kg: number;
  weight_3m_kg: number | null;
  weight_6m_kg: number | null;
  cc_cm: number | null;
  bmi: number | null;
  wl_pct_3m: number | null;
  wl_pct_6m: number | null;
  mna_q_a: number | null;
  mna_q_b: number | null;
  mna_q_c: number | null;
  mna_q_d: number | null;
  mna_q_e: number | null;
  mna_q_f: number | null;
  mna_total: number | null;
  mna_category: string | null;
  glim_weight_loss: number;
  glim_low_bmi: number;
  glim_muscle: string;
  glim_intake: number;
  glim_inflam: number;
  glim_chronic: number;
  glim_diagnosed: number | null;
  glim_severity: string | null;
  recommendations: string[];
  reasons: string[];
  isocal_recommendation: IsocalRecommendation;
  created_at: string;
}

export interface ChartDataPoint {
  assess_date: string;
  weight_kg: number;
  bmi: number | null;
  mna_total: number | null;
}

// --- Patient API ---
export const patientsApi = {
  list: (q?: string) => apiFetch<Patient[]>(`/api/patients${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  get: (id: number) => apiFetch<Patient>(`/api/patients/${id}`),
  create: (data: Partial<Patient>) => apiFetch<Patient>("/api/patients", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<Patient>) => apiFetch<Patient>(`/api/patients/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  delete: (id: number) => apiFetch<void>(`/api/patients/${id}`, { method: "DELETE" }),
};

// --- Assessment API ---
export const assessmentsApi = {
  create: (data: unknown) => apiFetch<Assessment>("/api/assessments", { method: "POST", body: JSON.stringify(data) }),
  get: (id: number) => apiFetch<Assessment>(`/api/assessments/${id}`),
  listForPatient: (patientId: number) => apiFetch<Assessment[]>(`/api/patients/${patientId}/assessments`),
  chartData: (patientId: number) => apiFetch<{ data: ChartDataPoint[] }>(`/api/patients/${patientId}/assessments/chart`),
};

// --- Export ---
export const exportApi = {
  csvUrl: (patientId: number) => `${API_BASE}/api/export/patients/${patientId}/csv`,
  excelUrl: (patientId: number) => `${API_BASE}/api/export/patients/${patientId}/excel`,
  pdfUrl: (assessmentId: number) => `${API_BASE}/api/assessments/${assessmentId}/pdf`,
};
```

- [ ] **Step 4: Write root layout**

Create `frontend/app/layout.tsx`:

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "低栄養診断ツール — MNA-SF / GLIM",
  description: "MNA-SFスクリーニングとGLIM基準による低栄養診断ツール",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body className={`${inter.className} bg-gray-50 min-h-screen`}>
        <header className="bg-[#1a56a4] text-white px-6 py-3">
          <h1 className="text-lg font-bold">低栄養診断ツール</h1>
          <p className="text-sm text-blue-200">MNA-SF / GLIM Nutrition Assessment</p>
        </header>
        <main className="max-w-6xl mx-auto px-4 py-6">{children}</main>
        <Toaster />
      </body>
    </html>
  );
}
```

- [ ] **Step 5: Verify dev server starts**

```bash
cd frontend && npm run dev
# Visit http://localhost:3000 → header renders
```

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold Next.js frontend with API client and layout"
```

---

### Task 10: Patient list page

**Files:**
- Create: `frontend/app/patients/page.tsx`
- Create: `frontend/components/patient-form.tsx`

- [ ] **Step 1: Write patient list page**

Create `frontend/app/patients/page.tsx`:

```tsx
"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { patientsApi, Patient } from "@/lib/api";
import { PatientForm } from "@/components/patient-form";

const GENDER_LABELS: Record<string, string> = {
  male: "男性", female: "女性", other: "その他",
};

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);

  const load = useCallback(async () => {
    const data = await patientsApi.list(search || undefined);
    setPatients(data);
  }, [search]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <Input
          placeholder="患者ID または 氏名で検索..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-[#1a56a4] hover:bg-[#1648b0]">＋ 患者追加</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>患者登録</DialogTitle>
            </DialogHeader>
            <PatientForm
              onSaved={() => { setDialogOpen(false); load(); }}
            />
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>患者ID</TableHead>
                <TableHead>氏名</TableHead>
                <TableHead>性別</TableHead>
                <TableHead>生年月日</TableHead>
                <TableHead>更新日</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {patients.map((p) => (
                <TableRow key={p.id} className="cursor-pointer hover:bg-blue-50">
                  <TableCell>
                    <Link href={`/patients/${p.id}`} className="text-[#1a56a4] font-semibold hover:underline">
                      {p.patient_code}
                    </Link>
                  </TableCell>
                  <TableCell>{p.name || "—"}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{GENDER_LABELS[p.gender] || p.gender}</Badge>
                  </TableCell>
                  <TableCell>{p.birth_date || "—"}</TableCell>
                  <TableCell className="text-gray-500 text-sm">
                    {p.updated_at ? new Date(p.updated_at).toLocaleDateString("ja-JP") : "—"}
                  </TableCell>
                </TableRow>
              ))}
              {patients.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-gray-400 py-8">
                    患者が登録されていません
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Write patient form component**

Create `frontend/components/patient-form.tsx`:

```tsx
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { patientsApi, Patient } from "@/lib/api";

const schema = z.object({
  patient_code: z.string().min(1, "患者IDは必須です"),
  name: z.string().default(""),
  gender: z.enum(["male", "female", "other"]),
  birth_date: z.string().optional(),
  notes: z.string().default(""),
});

type FormData = z.infer<typeof schema>;

interface Props {
  patient?: Patient;
  onSaved: () => void;
}

export function PatientForm({ patient, onSaved }: Props) {
  const { register, handleSubmit, setValue, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: patient
      ? { patient_code: patient.patient_code, name: patient.name, gender: patient.gender as "male" | "female" | "other", birth_date: patient.birth_date || "", notes: patient.notes }
      : { gender: "male" },
  });

  const onSubmit = async (data: FormData) => {
    if (patient) {
      await patientsApi.update(patient.id, data);
    } else {
      await patientsApi.create(data);
    }
    onSaved();
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <Label>患者ID *</Label>
        <Input {...register("patient_code")} placeholder="PT-0001" />
        {errors.patient_code && <p className="text-red-500 text-sm mt-1">{errors.patient_code.message}</p>}
      </div>
      <div>
        <Label>氏名</Label>
        <Input {...register("name")} />
      </div>
      <div>
        <Label>性別 *</Label>
        <Select defaultValue={patient?.gender || "male"} onValueChange={(v) => setValue("gender", v as "male" | "female" | "other")}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="male">男性</SelectItem>
            <SelectItem value="female">女性</SelectItem>
            <SelectItem value="other">その他</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label>生年月日</Label>
        <Input type="date" {...register("birth_date")} />
      </div>
      <div>
        <Label>備考</Label>
        <Input {...register("notes")} />
      </div>
      <Button type="submit" disabled={isSubmitting} className="w-full bg-[#1a56a4]">
        {isSubmitting ? "保存中..." : patient ? "更新" : "登録"}
      </Button>
    </form>
  );
}
```

- [ ] **Step 3: Add redirect from root**

Create `frontend/app/page.tsx`:

```tsx
import { redirect } from "next/navigation";
export default function Home() {
  redirect("/patients");
}
```

- [ ] **Step 4: Verify patient list renders**

```bash
cd frontend && npm run dev
# Visit http://localhost:3000/patients → empty table with add button
```

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: add patient list page with search and create dialog"
```

---

### Task 11: Patient detail page with chart

**Files:**
- Create: `frontend/app/patients/[id]/page.tsx`
- Create: `frontend/components/assessment-chart.tsx`

- [ ] **Step 1: Write the chart component**

Create `frontend/components/assessment-chart.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { assessmentsApi, ChartDataPoint } from "@/lib/api";

interface Props {
  patientId: number;
}

export function AssessmentChart({ patientId }: Props) {
  const [data, setData] = useState<ChartDataPoint[]>([]);

  useEffect(() => {
    assessmentsApi.chartData(patientId).then((res) => setData(res.data));
  }, [patientId]);

  if (data.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-gray-400">
          評価データがありません
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">経時変化グラフ</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="assess_date" fontSize={11} />
            <YAxis yAxisId="left" fontSize={11} />
            <YAxis yAxisId="right" orientation="right" fontSize={11} />
            <Tooltip />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="weight_kg" stroke="#1a56a4" name="体重(kg)" strokeWidth={2} />
            <Line yAxisId="left" type="monotone" dataKey="bmi" stroke="#b45309" name="BMI" strokeWidth={2} />
            <Line yAxisId="right" type="monotone" dataKey="mna_total" stroke="#1a7a4a" name="MNA-SF" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Write the patient detail page**

Create `frontend/app/patients/[id]/page.tsx`:

```tsx
"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { patientsApi, assessmentsApi, exportApi, Patient, Assessment } from "@/lib/api";
import { PatientForm } from "@/components/patient-form";
import { AssessmentChart } from "@/components/assessment-chart";

const GENDER_LABELS: Record<string, string> = { male: "男性", female: "女性", other: "その他" };
const CATEGORY_STYLES: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  normal: { label: "栄養良好", variant: "default" },
  risk: { label: "リスクあり", variant: "secondary" },
  severe: { label: "低栄養", variant: "destructive" },
};

export default function PatientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const patientId = Number(params.id);

  const [patient, setPatient] = useState<Patient | null>(null);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [editOpen, setEditOpen] = useState(false);

  const load = useCallback(async () => {
    const [p, a] = await Promise.all([
      patientsApi.get(patientId),
      assessmentsApi.listForPatient(patientId),
    ]);
    setPatient(p);
    setAssessments(a);
  }, [patientId]);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async () => {
    if (!confirm("この患者を削除しますか？関連する評価も全て削除されます。")) return;
    await patientsApi.delete(patientId);
    router.push("/patients");
  };

  if (!patient) return <div className="text-center py-8 text-gray-400">読み込み中...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link href="/patients" className="text-sm text-gray-500 hover:underline">← 患者一覧</Link>
          <h2 className="text-xl font-bold mt-1">{patient.patient_code} — {patient.name || "氏名未登録"}</h2>
        </div>
        <div className="flex gap-2">
          <Dialog open={editOpen} onOpenChange={setEditOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">編集</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>患者情報の編集</DialogTitle></DialogHeader>
              <PatientForm patient={patient} onSaved={() => { setEditOpen(false); load(); }} />
            </DialogContent>
          </Dialog>
          <Button variant="destructive" onClick={handleDelete}>削除</Button>
        </div>
      </div>

      {/* Patient info card */}
      <Card>
        <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4 py-4">
          <div><span className="text-gray-500 text-sm">性別</span><p className="font-medium">{GENDER_LABELS[patient.gender]}</p></div>
          <div><span className="text-gray-500 text-sm">生年月日</span><p className="font-medium">{patient.birth_date || "—"}</p></div>
          <div><span className="text-gray-500 text-sm">備考</span><p className="font-medium">{patient.notes || "—"}</p></div>
          <div><span className="text-gray-500 text-sm">評価回数</span><p className="font-medium">{assessments.length}回</p></div>
        </CardContent>
      </Card>

      {/* Chart */}
      <AssessmentChart patientId={patientId} />

      {/* Assessment history + actions */}
      <div className="flex items-center justify-between">
        <h3 className="font-bold">評価履歴</h3>
        <div className="flex gap-2">
          <a href={exportApi.csvUrl(patientId)} download>
            <Button variant="outline" size="sm">CSV</Button>
          </a>
          <a href={exportApi.excelUrl(patientId)} download>
            <Button variant="outline" size="sm">Excel</Button>
          </a>
          <Link href={`/assess/new?patient=${patientId}`}>
            <Button className="bg-[#1a56a4]">新規評価</Button>
          </Link>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>評価日</TableHead>
                <TableHead>年齢</TableHead>
                <TableHead>BMI</TableHead>
                <TableHead>MNA-SF</TableHead>
                <TableHead>GLIM</TableHead>
                <TableHead>重症度</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {assessments.map((a) => {
                const cat = CATEGORY_STYLES[a.mna_category || ""] || { label: "—", variant: "outline" as const };
                return (
                  <TableRow key={a.id} className="cursor-pointer hover:bg-blue-50">
                    <TableCell>
                      <Link href={`/assess/${a.id}`} className="text-[#1a56a4] hover:underline">{a.assess_date}</Link>
                    </TableCell>
                    <TableCell>{a.age_at_assess}歳</TableCell>
                    <TableCell>{a.bmi?.toFixed(1) || "—"}</TableCell>
                    <TableCell>
                      <Badge variant={cat.variant}>{a.mna_total ?? "—"} / 14 {cat.label}</Badge>
                    </TableCell>
                    <TableCell>{a.glim_diagnosed ? "低栄養" : "—"}</TableCell>
                    <TableCell>{a.glim_severity === "stage2" ? "Stage 2" : a.glim_severity === "stage1" ? "Stage 1" : "—"}</TableCell>
                  </TableRow>
                );
              })}
              {assessments.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-gray-400 py-8">評価履歴がありません</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Step 3: Verify page renders**

```bash
cd frontend && npm run dev
# Visit http://localhost:3000/patients/1 → patient detail with chart
```

- [ ] **Step 4: Commit**

```bash
git add frontend/
git commit -m "feat: add patient detail page with assessment chart and history"
```

---

### Task 12: Assessment wizard (Steps 1-3)

**Files:**
- Create: `frontend/app/assess/new/page.tsx`
- Create: `frontend/components/wizard/step-1.tsx`
- Create: `frontend/components/wizard/step-2-mna.tsx`
- Create: `frontend/components/wizard/step-3-glim.tsx`

- [ ] **Step 1: Write Step 1 component (patient info)**

Create `frontend/components/wizard/step-1.tsx`:

```tsx
"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";

interface Step1Data {
  assess_date: string;
  age_at_assess: number;
  height_cm: number;
  weight_kg: number;
  weight_3m_kg: number | null;
  weight_6m_kg: number | null;
  weight_3m_unknown: boolean;
  weight_6m_unknown: boolean;
  cc_cm: number | null;
}

interface Props {
  data: Step1Data;
  onChange: (data: Step1Data) => void;
}

export function Step1({ data, onChange }: Props) {
  const update = (patch: Partial<Step1Data>) => onChange({ ...data, ...patch });

  const bmi = data.weight_kg && data.height_cm
    ? (data.weight_kg / ((data.height_cm / 100) ** 2)).toFixed(1)
    : "—";

  const wlPct3m = data.weight_kg && data.weight_3m_kg
    ? (((data.weight_3m_kg - data.weight_kg) / data.weight_3m_kg) * 100).toFixed(1)
    : null;

  const wlPct6m = data.weight_kg && data.weight_6m_kg
    ? (((data.weight_6m_kg - data.weight_kg) / data.weight_6m_kg) * 100).toFixed(1)
    : null;

  return (
    <div className="space-y-4">
      <h3 className="font-bold text-[#1a56a4]">ステップ 1: 患者基本情報</h3>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>評価日 *</Label>
          <Input type="date" value={data.assess_date} onChange={(e) => update({ assess_date: e.target.value })} />
        </div>
        <div>
          <Label>年齢 *</Label>
          <Input type="number" value={data.age_at_assess || ""} onChange={(e) => update({ age_at_assess: Number(e.target.value) })} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>身長 (cm) *</Label>
          <Input type="number" step="0.1" value={data.height_cm || ""} onChange={(e) => update({ height_cm: Number(e.target.value) })} />
        </div>
        <div>
          <Label>現在体重 (kg) *</Label>
          <Input type="number" step="0.1" value={data.weight_kg || ""} onChange={(e) => update({ weight_kg: Number(e.target.value) })} />
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-md p-3 text-sm">
        BMI: <strong>{bmi}</strong>
        {wlPct3m && <> | 3M体重減少率: <strong>{wlPct3m}%</strong></>}
        {wlPct6m && <> | 6M体重減少率: <strong>{wlPct6m}%</strong></>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Label>3ヶ月前体重 (kg)</Label>
            <div className="flex items-center gap-1">
              <Checkbox
                checked={data.weight_3m_unknown}
                onCheckedChange={(v) => update({ weight_3m_unknown: !!v, weight_3m_kg: null })}
              />
              <span className="text-xs text-gray-500">不明</span>
            </div>
          </div>
          <Input
            type="number" step="0.1"
            disabled={data.weight_3m_unknown}
            value={data.weight_3m_kg ?? ""}
            onChange={(e) => update({ weight_3m_kg: e.target.value ? Number(e.target.value) : null })}
          />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <Label>6ヶ月前体重 (kg)</Label>
            <div className="flex items-center gap-1">
              <Checkbox
                checked={data.weight_6m_unknown}
                onCheckedChange={(v) => update({ weight_6m_unknown: !!v, weight_6m_kg: null })}
              />
              <span className="text-xs text-gray-500">不明</span>
            </div>
          </div>
          <Input
            type="number" step="0.1"
            disabled={data.weight_6m_unknown}
            value={data.weight_6m_kg ?? ""}
            onChange={(e) => update({ weight_6m_kg: e.target.value ? Number(e.target.value) : null })}
          />
        </div>
      </div>

      <div>
        <Label>下腿周囲長 CC (cm)</Label>
        <Input
          type="number" step="0.1"
          value={data.cc_cm ?? ""}
          onChange={(e) => update({ cc_cm: e.target.value ? Number(e.target.value) : null })}
        />
        <p className="text-xs text-gray-500 mt-1">BMIが測定できない場合のMNA-SF問F代替</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Write Step 2 component (MNA-SF)**

Create `frontend/components/wizard/step-2-mna.tsx`:

```tsx
"use client";

import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Badge } from "@/components/ui/badge";

interface MNAData {
  q_a: number | null;
  q_b: number | null;
  q_c: number | null;
  q_d: number | null;
  q_e: number | null;
  q_f: number | null;
}

interface Props {
  data: MNAData;
  autoEstimates: { q_b: number | null; q_f: number | null };
  onChange: (data: MNAData) => void;
}

const QUESTIONS = [
  {
    key: "q_a" as const, label: "問A: 食事量の変化（過去3ヶ月）",
    options: [
      { value: 0, label: "著しい食事量の減少" },
      { value: 1, label: "中程度の食事量の減少" },
      { value: 2, label: "食事量の減少なし" },
    ],
  },
  {
    key: "q_b" as const, label: "問B: 体重減少（過去3ヶ月）",
    options: [
      { value: 0, label: "3kg以上の減少" },
      { value: 1, label: "わからない" },
      { value: 2, label: "1〜3kgの減少" },
      { value: 3, label: "体重減少なし" },
    ],
  },
  {
    key: "q_c" as const, label: "問C: 移動能力",
    options: [
      { value: 0, label: "寝たきりまたは車椅子" },
      { value: 1, label: "ベッド・車椅子から離れられるが外出不可" },
      { value: 2, label: "自由に外出できる" },
    ],
  },
  {
    key: "q_d" as const, label: "問D: 過去3ヶ月間の精神的ストレス・急性疾患",
    options: [
      { value: 0, label: "はい" },
      { value: 2, label: "いいえ" },
    ],
  },
  {
    key: "q_e" as const, label: "問E: 神経・精神的問題",
    options: [
      { value: 0, label: "強度の認知症またはうつ状態" },
      { value: 1, label: "軽度の認知症" },
      { value: 2, label: "精神的問題なし" },
    ],
  },
  {
    key: "q_f" as const, label: "問F: BMI（またはCC）",
    options: [
      { value: 0, label: "BMI 19未満 / CC 31cm未満" },
      { value: 1, label: "BMI 19以上 21未満" },
      { value: 2, label: "BMI 21以上 23未満" },
      { value: 3, label: "BMI 23以上 / CC 31cm以上" },
    ],
  },
];

export function Step2MNA({ data, autoEstimates, onChange }: Props) {
  const values = [data.q_a, data.q_b, data.q_c, data.q_d, data.q_e, data.q_f];
  const total = values.every((v) => v !== null) ? values.reduce((s, v) => s! + v!, 0) : null;
  const maxScore = 14;

  const getScoreColor = () => {
    if (total === null) return "bg-gray-200";
    if (total >= 12) return "bg-[#1a7a4a]";
    if (total >= 8) return "bg-[#b45309]";
    return "bg-[#c0392b]";
  };

  const getLabel = () => {
    if (total === null) return "未入力";
    if (total >= 12) return "栄養良好";
    if (total >= 8) return "低栄養のリスクあり";
    return "低栄養の可能性";
  };

  return (
    <div className="space-y-4">
      <h3 className="font-bold text-[#1a56a4]">ステップ 2: MNA-SF スクリーニング</h3>

      {/* Score bar */}
      <div className="bg-gray-100 rounded-lg p-3">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium">MNA-SF スコア</span>
          <Badge className={getScoreColor()}>{total ?? "—"} / {maxScore} — {getLabel()}</Badge>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all ${getScoreColor()}`}
            style={{ width: `${total !== null ? (total / maxScore) * 100 : 0}%` }}
          />
        </div>
      </div>

      {QUESTIONS.map((q) => {
        const autoValue = q.key === "q_b" ? autoEstimates.q_b : q.key === "q_f" ? autoEstimates.q_f : null;
        return (
          <div key={q.key} className="border rounded-lg p-4 bg-white">
            <Label className="text-sm font-semibold">
              {q.label}
              {autoValue !== null && data[q.key] === null && (
                <span className="ml-2 text-blue-500 text-xs cursor-pointer" onClick={() => onChange({ ...data, [q.key]: autoValue })}>
                  [自動推定値: {autoValue}点 — クリックで適用]
                </span>
              )}
              {autoValue !== null && data[q.key] !== null && data[q.key] === autoValue && (
                <span className="ml-2 text-green-600 text-xs">✓ 自動推定値を使用中</span>
              )}
            </Label>
            <RadioGroup
              value={data[q.key]?.toString() ?? ""}
              onValueChange={(v) => onChange({ ...data, [q.key]: Number(v) })}
              className="mt-2 space-y-1"
            >
              {q.options.map((opt) => (
                <div key={opt.value} className="flex items-center space-x-2">
                  <RadioGroupItem value={opt.value.toString()} id={`${q.key}-${opt.value}`} />
                  <Label htmlFor={`${q.key}-${opt.value}`} className="font-normal cursor-pointer">
                    {opt.label} <span className="text-gray-400">({opt.value}点)</span>
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 3: Write Step 3 component (GLIM)**

Create `frontend/components/wizard/step-3-glim.tsx`:

```tsx
"use client";

import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface GLIMData {
  weight_loss: number;
  low_bmi: number;
  muscle: string;
  intake: number;
  inflam: number;
  chronic: number;
}

interface Props {
  data: GLIMData;
  autoEstimates: { weight_loss: boolean; low_bmi: boolean };
  onChange: (data: GLIMData) => void;
}

export function Step3GLIM({ data, autoEstimates, onChange }: Props) {
  const update = (patch: Partial<GLIMData>) => onChange({ ...data, ...patch });

  const phenotypicMet = data.weight_loss || data.low_bmi || data.muscle !== "none";
  const etiologicMet = data.intake || data.inflam || data.chronic;

  return (
    <div className="space-y-4">
      <h3 className="font-bold text-[#1a56a4]">ステップ 3: GLIM 評価</h3>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">
            表現型基準（1項目以上で充足）
            {phenotypicMet
              ? <span className="ml-2 text-green-600">✓ 充足</span>
              : <span className="ml-2 text-gray-400">未充足</span>
            }
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2">
            <Checkbox
              checked={!!data.weight_loss}
              onCheckedChange={(v) => update({ weight_loss: v ? 1 : 0 })}
            />
            <Label className="font-normal">
              意図しない体重減少
              {autoEstimates.weight_loss && <span className="text-blue-500 text-xs ml-1">(自動判定: 該当)</span>}
            </Label>
          </div>
          <div className="flex items-center gap-2">
            <Checkbox
              checked={!!data.low_bmi}
              onCheckedChange={(v) => update({ low_bmi: v ? 1 : 0 })}
            />
            <Label className="font-normal">
              低BMI（アジア人基準）
              {autoEstimates.low_bmi && <span className="text-blue-500 text-xs ml-1">(自動判定: 該当)</span>}
            </Label>
          </div>
          <div>
            <Label>筋肉量・筋量の低下</Label>
            <Select value={data.muscle} onValueChange={(v) => update({ muscle: v })}>
              <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">なし</SelectItem>
                <SelectItem value="mild">軽〜中等度</SelectItem>
                <SelectItem value="severe">高度</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">
            病因基準（1項目以上で充足）
            {etiologicMet
              ? <span className="ml-2 text-green-600">✓ 充足</span>
              : <span className="ml-2 text-gray-400">未充足</span>
            }
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2">
            <Checkbox checked={!!data.intake} onCheckedChange={(v) => update({ intake: v ? 1 : 0 })} />
            <Label className="font-normal">食事摂取量の低下 / 消化吸収障害</Label>
          </div>
          <div className="flex items-center gap-2">
            <Checkbox checked={!!data.inflam} onCheckedChange={(v) => update({ inflam: v ? 1 : 0 })} />
            <Label className="font-normal">急性疾患 / 外傷による炎症</Label>
          </div>
          <div className="flex items-center gap-2">
            <Checkbox checked={!!data.chronic} onCheckedChange={(v) => update({ chronic: v ? 1 : 0 })} />
            <Label className="font-normal">慢性疾患による炎症（中等度）</Label>
          </div>
        </CardContent>
      </Card>

      {phenotypicMet && etiologicMet && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">
          表現型基準・病因基準ともに充足 → <strong>低栄養と診断されます</strong>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Write the wizard page (orchestrating steps 1-3 + submit)**

Create `frontend/app/assess/new/page.tsx`:

```tsx
"use client";

import { useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Step1 } from "@/components/wizard/step-1";
import { Step2MNA } from "@/components/wizard/step-2-mna";
import { Step3GLIM } from "@/components/wizard/step-3-glim";
import { assessmentsApi } from "@/lib/api";

export default function NewAssessmentPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const patientId = Number(searchParams.get("patient"));

  const [step, setStep] = useState(1);
  const today = new Date().toISOString().slice(0, 10);

  const [step1, setStep1] = useState({
    assess_date: today, age_at_assess: 0, height_cm: 0, weight_kg: 0,
    weight_3m_kg: null as number | null, weight_6m_kg: null as number | null,
    weight_3m_unknown: false, weight_6m_unknown: false,
    cc_cm: null as number | null,
  });

  const [mna, setMna] = useState({
    q_a: null as number | null, q_b: null as number | null,
    q_c: null as number | null, q_d: null as number | null,
    q_e: null as number | null, q_f: null as number | null,
  });

  const [glim, setGlim] = useState({
    weight_loss: 0, low_bmi: 0, muscle: "none", intake: 0, inflam: 0, chronic: 0,
  });

  // Auto-estimates for MNA
  const bmi = step1.weight_kg && step1.height_cm
    ? step1.weight_kg / ((step1.height_cm / 100) ** 2)
    : null;

  const autoQB = (() => {
    if (!step1.weight_kg || !step1.weight_3m_kg) return null;
    const loss = step1.weight_3m_kg - step1.weight_kg;
    if (loss >= 3) return 0;
    if (loss > 0) return 2;
    return 3;
  })();

  const autoQF = (() => {
    if (bmi !== null) {
      if (bmi < 19) return 0;
      if (bmi < 21) return 1;
      if (bmi < 23) return 2;
      return 3;
    }
    if (step1.cc_cm !== null) return step1.cc_cm >= 31 ? 3 : 0;
    return null;
  })();

  // Auto-estimates for GLIM
  const autoWeightLoss = (() => {
    if (step1.weight_3m_kg && step1.weight_kg) {
      const pct = ((step1.weight_3m_kg - step1.weight_kg) / step1.weight_3m_kg) * 100;
      if (pct > 5) return true;
    }
    if (step1.weight_6m_kg && step1.weight_kg) {
      const pct = ((step1.weight_6m_kg - step1.weight_kg) / step1.weight_6m_kg) * 100;
      if (pct > 10) return true;
    }
    return false;
  })();

  const autoLowBmi = (() => {
    if (bmi === null) return false;
    return step1.age_at_assess >= 70 ? bmi < 22 : bmi < 20;
  })();

  const mnaTotal = [mna.q_a, mna.q_b, mna.q_c, mna.q_d, mna.q_e, mna.q_f].every((v) => v !== null)
    ? [mna.q_a, mna.q_b, mna.q_c, mna.q_d, mna.q_e, mna.q_f].reduce((s, v) => s! + v!, 0)
    : null;

  const skipGlim = mnaTotal !== null && mnaTotal >= 12;
  const totalSteps = skipGlim ? 2 : 3;

  const handleSubmit = async () => {
    const payload = {
      patient_id: patientId,
      assess_date: step1.assess_date,
      age_at_assess: step1.age_at_assess,
      height_cm: step1.height_cm,
      weight_kg: step1.weight_kg,
      weight_3m_kg: step1.weight_3m_kg,
      weight_6m_kg: step1.weight_6m_kg,
      cc_cm: step1.cc_cm,
      mna,
      glim: skipGlim ? { weight_loss: 0, low_bmi: 0, muscle: "none", intake: 0, inflam: 0, chronic: 0 } : glim,
    };
    const result = await assessmentsApi.create(payload);
    router.push(`/assess/${result.id}`);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      {/* Stepper */}
      <div className="flex items-center justify-center gap-2 text-sm">
        {Array.from({ length: totalSteps }, (_, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
              ${step >= i + 1 ? "bg-[#1a56a4] text-white" : "bg-gray-200 text-gray-500"}`}>
              {i + 1}
            </div>
            {i < totalSteps - 1 && <div className="w-8 h-px bg-gray-300" />}
          </div>
        ))}
      </div>

      <Card>
        <CardContent className="pt-6">
          {step === 1 && <Step1 data={step1} onChange={setStep1} />}
          {step === 2 && <Step2MNA data={mna} autoEstimates={{ q_b: autoQB, q_f: autoQF }} onChange={setMna} />}
          {step === 3 && !skipGlim && (
            <Step3GLIM data={glim} autoEstimates={{ weight_loss: autoWeightLoss, low_bmi: autoLowBmi }} onChange={setGlim} />
          )}
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" onClick={() => step > 1 ? setStep(step - 1) : router.back()} >
          {step > 1 ? "← 前へ" : "← キャンセル"}
        </Button>
        {step < totalSteps ? (
          <Button className="bg-[#1a56a4]" onClick={() => setStep(step + 1)}>次へ →</Button>
        ) : (
          <Button className="bg-[#1a7a4a] hover:bg-[#156b3e]" onClick={handleSubmit}>評価を保存</Button>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Verify wizard flow**

```bash
cd frontend && npm run dev
# Visit http://localhost:3000/assess/new?patient=1 → wizard renders with 3 steps
```

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: add 3-step assessment wizard with MNA-SF and GLIM"
```

---

### Task 13: Result screen with Isocal banner

**Files:**
- Create: `frontend/app/assess/[id]/page.tsx`
- Create: `frontend/components/isocal-banner.tsx`

- [ ] **Step 1: Write the Isocal banner component**

Create `frontend/components/isocal-banner.tsx`:

```tsx
"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { IsocalRecommendation } from "@/lib/api";

interface Props {
  recommendation: IsocalRecommendation;
}

export function IsocalBanner({ recommendation }: Props) {
  if (!recommendation.show) return null;

  return (
    <Card className="border-2 border-[#00a0e0] bg-gradient-to-r from-blue-50 to-white">
      <CardContent className="py-5 space-y-3">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 bg-[#00a0e0] rounded-lg flex items-center justify-center text-white text-xs font-bold shrink-0">
            Isocal<br/>100
          </div>
          <div className="flex-1">
            <h4 className="font-bold text-lg text-[#00508c]">{recommendation.product_name}</h4>
            <p className="text-sm text-gray-700 mt-1">{recommendation.description}</p>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-md p-3 text-xs text-gray-600 leading-relaxed whitespace-pre-line">
          {recommendation.permitted_claim}
        </div>

        <div className="flex gap-3">
          <a href={recommendation.brand_url} target="_blank" rel="noopener noreferrer">
            <Button variant="outline" className="border-[#00a0e0] text-[#00508c] hover:bg-blue-50">
              製品について詳しく
            </Button>
          </a>
          <a href={recommendation.purchase_url} target="_blank" rel="noopener noreferrer">
            <Button className="bg-[#00a0e0] hover:bg-[#0088c0] text-white">
              ご購入はこちら
            </Button>
          </a>
        </div>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Write the result page**

Create `frontend/app/assess/[id]/page.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { assessmentsApi, exportApi, Assessment } from "@/lib/api";
import { IsocalBanner } from "@/components/isocal-banner";

const BANNER_STYLES = {
  normal: { bg: "bg-green-50", border: "border-green-500", text: "text-green-700", label: "栄養良好（MNA-SF ≥12）" },
  risk: { bg: "bg-yellow-50", border: "border-yellow-500", text: "text-yellow-700", label: "低栄養のリスクあり" },
  severe: { bg: "bg-red-50", border: "border-red-500", text: "text-red-700", label: "低栄養の可能性" },
};

export default function AssessmentResultPage() {
  const params = useParams();
  const assessmentId = Number(params.id);
  const [assessment, setAssessment] = useState<Assessment | null>(null);

  useEffect(() => {
    assessmentsApi.get(assessmentId).then(setAssessment);
  }, [assessmentId]);

  if (!assessment) return <div className="text-center py-8 text-gray-400">読み込み中...</div>;

  const a = assessment;
  const category = a.mna_category || "risk";
  const banner = BANNER_STYLES[category as keyof typeof BANNER_STYLES] || BANNER_STYLES.risk;

  const glimLabel = a.glim_diagnosed
    ? a.glim_severity === "stage2" ? "低栄養（Stage 2: 高度）" : "低栄養（Stage 1: 中等度）"
    : a.mna_category === "normal" ? null : "低栄養非該当（要観察）";

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <Link href={`/patients/${a.patient_id}`} className="text-sm text-gray-500 hover:underline">← 患者詳細に戻る</Link>

      <h2 className="text-xl font-bold">評価結果 — {a.assess_date}</h2>

      {/* Diagnosis banner */}
      <div className={`${banner.bg} border-2 ${banner.border} rounded-lg p-4`}>
        <p className={`text-lg font-bold ${banner.text}`}>{banner.label}</p>
        {glimLabel && <p className={`text-sm mt-1 ${banner.text}`}>{glimLabel}</p>}
      </div>

      {/* Score summary */}
      <Card>
        <CardHeader><CardTitle className="text-sm">スコアサマリ</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div><span className="text-gray-500 text-xs">MNA-SF</span><p className="text-lg font-bold">{a.mna_total ?? "—"} / 14</p></div>
          <div><span className="text-gray-500 text-xs">BMI</span><p className="text-lg font-bold">{a.bmi?.toFixed(1) ?? "—"}</p></div>
          <div><span className="text-gray-500 text-xs">体重減少率(3M)</span><p className="text-lg font-bold">{a.wl_pct_3m ? `${a.wl_pct_3m.toFixed(1)}%` : "—"}</p></div>
          <div><span className="text-gray-500 text-xs">体重減少率(6M)</span><p className="text-lg font-bold">{a.wl_pct_6m ? `${a.wl_pct_6m.toFixed(1)}%` : "—"}</p></div>
        </CardContent>
      </Card>

      {/* GLIM breakdown (if applicable) */}
      {a.glim_diagnosed !== null && a.reasons.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-sm">GLIM 評価内訳</CardTitle></CardHeader>
          <CardContent>
            <ul className="space-y-1">
              {a.reasons.map((r, i) => (
                <li key={i} className="text-sm flex items-start gap-2">
                  <span className="text-red-500 mt-0.5">●</span>
                  {r}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      <Card>
        <CardHeader><CardTitle className="text-sm">推奨アクション</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {a.recommendations.map((rec, i) => (
            <div key={i} className={`p-3 rounded-md text-sm ${
              a.glim_severity === "stage2" ? "bg-red-50 border border-red-200" : "bg-yellow-50 border border-yellow-200"
            }`}>
              {rec}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Isocal 100 recommendation */}
      <IsocalBanner recommendation={a.isocal_recommendation} />

      {/* Actions */}
      <div className="flex gap-3">
        <a href={exportApi.pdfUrl(a.id)} download>
          <Button variant="outline">PDF出力</Button>
        </a>
        <Link href={`/patients/${a.patient_id}`}>
          <Button variant="outline">患者詳細に戻る</Button>
        </Link>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verify result page and Isocal banner**

```bash
cd frontend && npm run dev
# Create a patient, run an assessment with GLIM malnutrition → Isocal banner appears
# Run an assessment with MNA ≥12 → Isocal banner does NOT appear
```

- [ ] **Step 4: Commit**

```bash
git add frontend/
git commit -m "feat: add assessment result page with Isocal 100 recommendation banner"
```

---

## Phase 4: Integration Testing and Polish

### Task 14: End-to-end smoke tests

**Files:**
- Create: `frontend/__tests__/smoke.test.tsx`

- [ ] **Step 1: Write frontend smoke tests**

Create `frontend/__tests__/smoke.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { IsocalBanner } from "@/components/isocal-banner";

describe("IsocalBanner", () => {
  it("renders when show is true", () => {
    render(
      <IsocalBanner
        recommendation={{
          show: true,
          product_name: "アイソカル® 100",
          description: "100mlで200kcal",
          permitted_claim: "本品は、食事として摂取すべき...",
          brand_url: "https://example.com/brand",
          purchase_url: "https://example.com/buy",
        }}
      />
    );
    expect(screen.getByText("アイソカル® 100")).toBeDefined();
    expect(screen.getByText("製品について詳しく")).toBeDefined();
    expect(screen.getByText("ご購入はこちら")).toBeDefined();
  });

  it("renders nothing when show is false", () => {
    const { container } = render(
      <IsocalBanner
        recommendation={{
          show: false,
          product_name: "",
          description: "",
          permitted_claim: "",
          brand_url: "",
          purchase_url: "",
        }}
      />
    );
    expect(container.innerHTML).toBe("");
  });
});
```

- [ ] **Step 2: Run frontend tests**

```bash
cd frontend && npx vitest run
# Expected: PASS
```

- [ ] **Step 3: Run full backend test suite**

```bash
cd backend && python -m pytest -v --tb=short
# Expected: all PASS
```

- [ ] **Step 4: Manual end-to-end test**

Start both servers and verify:

```bash
# Terminal 1
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev
```

Test flow:
1. `/patients` — create patient "PT-0001 田中太郎"
2. `/patients/1` — verify patient card, empty chart
3. Click "新規評価" → wizard Step 1: fill in data (weight 50kg, 3M-ago 55kg, height 160cm, age 75)
4. Step 2: fill MNA-SF with low scores → total < 12
5. Step 3: check GLIM criteria (weight_loss + intake)
6. Submit → result page shows red banner + Isocal 100 recommendation
7. Click PDF → download works
8. Go back → chart shows data point
9. CSV/Excel export buttons work
10. Create second assessment with MNA ≥ 12 → no Isocal banner

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "test: add frontend smoke tests and verify E2E flow"
```

---

### Task 15: Final cleanup and README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README for web version**

Update the root `README.md` to document:
- New architecture (Next.js + FastAPI)
- How to install and run both servers
- Environment variables (.env)
- Available API endpoints
- Development workflow

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README for web version architecture"
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | 1-7 | Backend: scaffolding, DB, schemas, logic, CRUD, API routes, exports |
| 2 | 8 | Figma: UI design for all 7 screens |
| 3 | 9-13 | Frontend: scaffolding, patient pages, wizard, result + Isocal banner |
| 4 | 14-15 | Testing, E2E verification, documentation |

**Total: 15 tasks, ~60 commits**
