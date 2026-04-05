"""Tests for diagnostic logic."""
from __future__ import annotations
from app.core.logic import (
    calc_bmi, calc_weight_loss_pct, is_low_bmi_glim, is_low_bmi_severe,
    interpret_mna_sf_score, interpret_weight_loss_glim, calc_glim_severity,
    auto_estimate_mna_q_b, auto_estimate_mna_q_f_bmi, auto_estimate_mna_q_f_cc,
)
from app.core.recommendations import get_recommendations, should_show_isocal


def test_calc_bmi_normal():
    assert round(calc_bmi(60.0, 165.0), 1) == 22.0

def test_calc_bmi_none():
    assert calc_bmi(None, 165.0) is None
    assert calc_bmi(60.0, 0) is None

def test_weight_loss_pct():
    assert round(calc_weight_loss_pct(54.0, 60.0), 1) == 10.0

def test_weight_loss_pct_none():
    assert calc_weight_loss_pct(None, 60.0) is None

def test_low_bmi_glim_elderly():
    assert is_low_bmi_glim(21.5, 75) is True
    assert is_low_bmi_glim(22.5, 75) is False

def test_low_bmi_glim_young():
    assert is_low_bmi_glim(19.5, 60) is True
    assert is_low_bmi_glim(20.5, 60) is False

def test_low_bmi_severe_elderly():
    assert is_low_bmi_severe(19.5, 75) is True
    assert is_low_bmi_severe(20.5, 75) is False

def test_low_bmi_severe_young():
    assert is_low_bmi_severe(18.0, 60) is True
    assert is_low_bmi_severe(19.0, 60) is False

def test_mna_normal():
    assert interpret_mna_sf_score(13)["category"] == "normal"

def test_mna_risk():
    assert interpret_mna_sf_score(10)["category"] == "risk"

def test_mna_severe():
    assert interpret_mna_sf_score(5)["category"] == "severe"

def test_mna_none():
    assert interpret_mna_sf_score(None)["category"] == "unknown"

def test_auto_q_b_big_loss():
    assert auto_estimate_mna_q_b(57.0, 61.0) == 0

def test_auto_q_b_small_loss():
    assert auto_estimate_mna_q_b(59.0, 61.0) == 2

def test_auto_q_b_no_loss():
    assert auto_estimate_mna_q_b(61.0, 60.0) == 3

def test_auto_q_f_bmi_low():
    assert auto_estimate_mna_q_f_bmi(18.0) == 0

def test_auto_q_f_bmi_high():
    assert auto_estimate_mna_q_f_bmi(24.0) == 3

def test_auto_q_f_cc_low():
    assert auto_estimate_mna_q_f_cc(29.0) == 0

def test_auto_q_f_cc_high():
    assert auto_estimate_mna_q_f_cc(32.0) == 3

def test_weight_loss_glim_moderate_3m():
    result = interpret_weight_loss_glim(7.0, None)
    assert result["present"] is True
    assert result["severe"] is False

def test_weight_loss_glim_severe_3m():
    result = interpret_weight_loss_glim(12.0, None)
    assert result["present"] is True
    assert result["severe"] is True

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

def test_recommendations_normal():
    recs = get_recommendations("normal", False, None)
    assert len(recs) == 1

def test_recommendations_stage2():
    recs = get_recommendations("severe", True, "stage2")
    assert any("Stage 2" in r for r in recs)

def test_isocal_show():
    assert should_show_isocal(True) is True

def test_isocal_hide():
    assert should_show_isocal(False) is False
    assert should_show_isocal(None) is False
