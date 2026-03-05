"""SQLite CRUD — ~/.nutrition_tool/data.db"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Optional

from models import Patient, Assessment, MNAAnswers, GLIMAnswers

DB_DIR = Path.home() / '.nutrition_tool'
DB_PATH = DB_DIR / 'data.db'

DDL = """
CREATE TABLE IF NOT EXISTS patients (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_code TEXT NOT NULL UNIQUE,
    name         TEXT,
    gender       TEXT NOT NULL,
    birth_date   TEXT,
    notes        TEXT DEFAULT '',
    created_at   TEXT DEFAULT (datetime('now','localtime')),
    updated_at   TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS assessments (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id       INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    assess_date      TEXT NOT NULL,
    age_at_assess    INTEGER NOT NULL,
    height_cm        REAL NOT NULL,
    weight_kg        REAL NOT NULL,
    weight_3m_kg     REAL,
    weight_6m_kg     REAL,
    cc_cm            REAL,
    bmi              REAL,
    wl_pct_3m        REAL,
    wl_pct_6m        REAL,
    mna_q_a          INTEGER,
    mna_q_b          INTEGER,
    mna_q_c          INTEGER,
    mna_q_d          INTEGER,
    mna_q_e          INTEGER,
    mna_q_f          INTEGER,
    mna_total        INTEGER,
    glim_weight_loss INTEGER DEFAULT 0,
    glim_low_bmi     INTEGER DEFAULT 0,
    glim_muscle      TEXT DEFAULT 'none',
    glim_intake      INTEGER DEFAULT 0,
    glim_inflam      INTEGER DEFAULT 0,
    glim_chronic     INTEGER DEFAULT 0,
    mna_category     TEXT,
    glim_diagnosed   INTEGER,
    glim_severity    TEXT,
    created_at       TEXT DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_assessments_patient
    ON assessments(patient_id, assess_date DESC);
"""


def _connect() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(DDL)


# ──────────────────────────────────────────────
# Patients
# ──────────────────────────────────────────────

def get_all_patients() -> list[Patient]:
    with _connect() as conn:
        rows = conn.execute(
            'SELECT * FROM patients ORDER BY updated_at DESC'
        ).fetchall()
    return [_row_to_patient(r) for r in rows]


def search_patients(query: str) -> list[Patient]:
    like = f'%{query}%'
    with _connect() as conn:
        rows = conn.execute(
            'SELECT * FROM patients WHERE patient_code LIKE ? OR name LIKE ? '
            'ORDER BY updated_at DESC',
            (like, like),
        ).fetchall()
    return [_row_to_patient(r) for r in rows]


def get_patient(patient_id: int) -> Optional[Patient]:
    with _connect() as conn:
        row = conn.execute(
            'SELECT * FROM patients WHERE id = ?', (patient_id,)
        ).fetchone()
    return _row_to_patient(row) if row else None


def insert_patient(p: Patient) -> int:
    with _connect() as conn:
        cur = conn.execute(
            'INSERT INTO patients (patient_code, name, gender, birth_date, notes) '
            'VALUES (?, ?, ?, ?, ?)',
            (p.patient_code, p.name, p.gender, p.birth_date, p.notes),
        )
        return cur.lastrowid


def update_patient(p: Patient) -> None:
    with _connect() as conn:
        conn.execute(
            'UPDATE patients SET patient_code=?, name=?, gender=?, birth_date=?, notes=?, '
            "updated_at=datetime('now','localtime') WHERE id=?",
            (p.patient_code, p.name, p.gender, p.birth_date, p.notes, p.id),
        )


def delete_patient(patient_id: int) -> None:
    with _connect() as conn:
        conn.execute('DELETE FROM patients WHERE id = ?', (patient_id,))


def patient_code_exists(code: str, exclude_id: Optional[int] = None) -> bool:
    with _connect() as conn:
        if exclude_id is not None:
            row = conn.execute(
                'SELECT 1 FROM patients WHERE patient_code = ? AND id != ?',
                (code, exclude_id),
            ).fetchone()
        else:
            row = conn.execute(
                'SELECT 1 FROM patients WHERE patient_code = ?', (code,)
            ).fetchone()
    return row is not None


def _row_to_patient(row: sqlite3.Row) -> Patient:
    return Patient(
        id=row['id'],
        patient_code=row['patient_code'],
        name=row['name'] or '',
        gender=row['gender'],
        birth_date=row['birth_date'],
        notes=row['notes'] or '',
        created_at=row['created_at'] or '',
        updated_at=row['updated_at'] or '',
    )


# ──────────────────────────────────────────────
# Assessments
# ──────────────────────────────────────────────

def get_assessments_for_patient(patient_id: int) -> list[Assessment]:
    with _connect() as conn:
        rows = conn.execute(
            'SELECT * FROM assessments WHERE patient_id = ? ORDER BY assess_date DESC',
            (patient_id,),
        ).fetchall()
    return [_row_to_assessment(r) for r in rows]


def get_assessment(assessment_id: int) -> Optional[Assessment]:
    with _connect() as conn:
        row = conn.execute(
            'SELECT * FROM assessments WHERE id = ?', (assessment_id,)
        ).fetchone()
    return _row_to_assessment(row) if row else None


def insert_assessment(a: Assessment) -> int:
    mna = a.mna
    glim = a.glim
    with _connect() as conn:
        cur = conn.execute(
            '''INSERT INTO assessments (
                patient_id, assess_date, age_at_assess, height_cm, weight_kg,
                weight_3m_kg, weight_6m_kg, cc_cm, bmi, wl_pct_3m, wl_pct_6m,
                mna_q_a, mna_q_b, mna_q_c, mna_q_d, mna_q_e, mna_q_f, mna_total,
                glim_weight_loss, glim_low_bmi, glim_muscle,
                glim_intake, glim_inflam, glim_chronic,
                mna_category, glim_diagnosed, glim_severity
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (
                a.patient_id, a.assess_date, a.age_at_assess,
                a.height_cm, a.weight_kg, a.weight_3m_kg, a.weight_6m_kg, a.cc_cm,
                a.bmi, a.wl_pct_3m, a.wl_pct_6m,
                mna.q_a, mna.q_b, mna.q_c, mna.q_d, mna.q_e, mna.q_f, mna.total,
                int(glim.weight_loss), int(glim.low_bmi), glim.muscle,
                int(glim.intake), int(glim.inflam), int(glim.chronic),
                a.mna_category,
                int(a.glim_diagnosed) if a.glim_diagnosed is not None else None,
                a.glim_severity,
            ),
        )
        # Update patient's updated_at
        conn.execute(
            "UPDATE patients SET updated_at=datetime('now','localtime') WHERE id=?",
            (a.patient_id,),
        )
        return cur.lastrowid


def delete_assessment(assessment_id: int) -> None:
    with _connect() as conn:
        conn.execute('DELETE FROM assessments WHERE id = ?', (assessment_id,))


def _row_to_assessment(row: sqlite3.Row) -> Assessment:
    mna = MNAAnswers(
        q_a=row['mna_q_a'],
        q_b=row['mna_q_b'],
        q_c=row['mna_q_c'],
        q_d=row['mna_q_d'],
        q_e=row['mna_q_e'],
        q_f=row['mna_q_f'],
    )
    glim = GLIMAnswers(
        weight_loss=row['glim_weight_loss'] or 0,
        low_bmi=row['glim_low_bmi'] or 0,
        muscle=row['glim_muscle'] or 'none',
        intake=row['glim_intake'] or 0,
        inflam=row['glim_inflam'] or 0,
        chronic=row['glim_chronic'] or 0,
    )
    diagnosed = row['glim_diagnosed']
    return Assessment(
        id=row['id'],
        patient_id=row['patient_id'],
        assess_date=row['assess_date'],
        age_at_assess=row['age_at_assess'],
        height_cm=row['height_cm'],
        weight_kg=row['weight_kg'],
        weight_3m_kg=row['weight_3m_kg'],
        weight_6m_kg=row['weight_6m_kg'],
        cc_cm=row['cc_cm'],
        bmi=row['bmi'],
        wl_pct_3m=row['wl_pct_3m'],
        wl_pct_6m=row['wl_pct_6m'],
        mna=mna,
        glim=glim,
        mna_category=row['mna_category'],
        glim_diagnosed=bool(diagnosed) if diagnosed is not None else None,
        glim_severity=row['glim_severity'],
        created_at=row['created_at'] or '',
    )
