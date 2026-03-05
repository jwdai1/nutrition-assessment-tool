"""データモデル定義（dataclasses）"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Patient:
    id: Optional[int]
    patient_code: str
    name: str
    gender: str           # 'male' | 'female' | 'other'
    birth_date: Optional[str]
    notes: str = ''
    created_at: str = ''
    updated_at: str = ''


@dataclass
class MNAAnswers:
    q_a: Optional[int] = None   # 0,1,2
    q_b: Optional[int] = None   # 0,1,2,3
    q_c: Optional[int] = None   # 0,1,2
    q_d: Optional[int] = None   # 0,2
    q_e: Optional[int] = None   # 0,1,2
    q_f: Optional[int] = None   # 0,1,2,3

    @property
    def total(self) -> Optional[int]:
        answers = [self.q_a, self.q_b, self.q_c, self.q_d, self.q_e, self.q_f]
        if any(a is None for a in answers):
            return None
        return sum(answers)


@dataclass
class GLIMAnswers:
    weight_loss: int = 0       # 0/1
    low_bmi: int = 0           # 0/1
    muscle: str = 'none'       # 'none'|'mild'|'severe'
    intake: int = 0            # 0/1
    inflam: int = 0            # 0/1
    chronic: int = 0           # 0/1


@dataclass
class Assessment:
    id: Optional[int]
    patient_id: int
    assess_date: str
    age_at_assess: int
    height_cm: float
    weight_kg: float
    weight_3m_kg: Optional[float] = None
    weight_6m_kg: Optional[float] = None
    cc_cm: Optional[float] = None
    bmi: Optional[float] = None
    wl_pct_3m: Optional[float] = None
    wl_pct_6m: Optional[float] = None
    mna: MNAAnswers = field(default_factory=MNAAnswers)
    glim: GLIMAnswers = field(default_factory=GLIMAnswers)
    mna_category: Optional[str] = None     # 'normal'|'risk'|'severe'
    glim_diagnosed: Optional[int] = None   # 0/1
    glim_severity: Optional[str] = None    # None|'stage1'|'stage2'
    created_at: str = ''
