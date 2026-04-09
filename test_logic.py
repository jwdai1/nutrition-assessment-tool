"""Unit tests for logic.py (pure functions, no Qt required)"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent))
import logic


# ──────────────────────────────────────────────
# calc_bmi
# ──────────────────────────────────────────────

class TestCalcBmi:
    def test_normal(self):
        bmi = logic.calc_bmi(60, 160)
        assert abs(bmi - 23.4375) < 0.001

    def test_none_weight(self):
        assert logic.calc_bmi(None, 160) is None

    def test_none_height(self):
        assert logic.calc_bmi(60, None) is None

    def test_zero_height(self):
        assert logic.calc_bmi(60, 0) is None

    def test_underweight(self):
        bmi = logic.calc_bmi(45, 170)
        assert bmi < 18.5

    def test_obese(self):
        bmi = logic.calc_bmi(100, 160)
        assert bmi > 30


# ──────────────────────────────────────────────
# calc_weight_loss_pct
# ──────────────────────────────────────────────

class TestCalcWeightLossPct:
    def test_5_percent_loss(self):
        pct = logic.calc_weight_loss_pct(47.5, 50.0)
        assert abs(pct - 5.0) < 0.001

    def test_no_loss(self):
        pct = logic.calc_weight_loss_pct(50, 50)
        assert pct == 0.0

    def test_weight_gain(self):
        pct = logic.calc_weight_loss_pct(52, 50)
        assert pct < 0

    def test_none_current(self):
        assert logic.calc_weight_loss_pct(None, 50) is None

    def test_none_previous(self):
        assert logic.calc_weight_loss_pct(50, None) is None

    def test_zero_previous(self):
        assert logic.calc_weight_loss_pct(50, 0) is None


# ──────────────────────────────────────────────
# is_low_bmi_glim
# ──────────────────────────────────────────────

class TestIsLowBmiGlim:
    # under 70: threshold <20
    def test_young_low(self):
        assert logic.is_low_bmi_glim(19.9, 65) is True

    def test_young_normal(self):
        assert logic.is_low_bmi_glim(20.0, 65) is False

    # 70+: threshold <22
    def test_elderly_low(self):
        assert logic.is_low_bmi_glim(21.9, 70) is True

    def test_elderly_normal(self):
        assert logic.is_low_bmi_glim(22.0, 70) is False

    def test_none_bmi(self):
        assert logic.is_low_bmi_glim(None, 65) is False


# ──────────────────────────────────────────────
# is_low_bmi_severe
# ──────────────────────────────────────────────

class TestIsLowBmiSevere:
    # under 70: threshold <18.5
    def test_young_severe(self):
        assert logic.is_low_bmi_severe(18.4, 60) is True

    def test_young_not_severe(self):
        assert logic.is_low_bmi_severe(18.5, 60) is False

    # 70+: threshold <20
    def test_elderly_severe(self):
        assert logic.is_low_bmi_severe(19.9, 75) is True

    def test_elderly_not_severe(self):
        assert logic.is_low_bmi_severe(20.0, 75) is False

    def test_none_bmi(self):
        assert logic.is_low_bmi_severe(None, 65) is False


# ──────────────────────────────────────────────
# interpret_mna_sf_score
# ──────────────────────────────────────────────

class TestInterpretMnaSfScore:
    def test_normal(self):
        r = logic.interpret_mna_sf_score(14)
        assert r['category'] == 'normal'

    def test_normal_boundary(self):
        r = logic.interpret_mna_sf_score(12)
        assert r['category'] == 'normal'

    def test_risk(self):
        r = logic.interpret_mna_sf_score(10)
        assert r['category'] == 'risk'

    def test_risk_boundary(self):
        r = logic.interpret_mna_sf_score(8)
        assert r['category'] == 'risk'

    def test_severe(self):
        r = logic.interpret_mna_sf_score(7)
        assert r['category'] == 'severe'

    def test_zero(self):
        r = logic.interpret_mna_sf_score(0)
        assert r['category'] == 'severe'

    def test_none(self):
        r = logic.interpret_mna_sf_score(None)
        assert r['category'] == 'unknown'

    def test_eleven_boundary(self):
        r = logic.interpret_mna_sf_score(11)
        assert r['category'] == 'risk'


# ──────────────────────────────────────────────
# interpret_weight_loss_glim
# ──────────────────────────────────────────────

class TestInterpretWeightLossGlim:
    def test_no_data(self):
        r = logic.interpret_weight_loss_glim(None, None)
        assert r['present'] is False
        assert r['severe'] is False

    def test_3m_moderate(self):
        r = logic.interpret_weight_loss_glim(7.0, None)
        assert r['present'] is True
        assert r['severe'] is False

    def test_3m_severe(self):
        r = logic.interpret_weight_loss_glim(11.0, None)
        assert r['present'] is True
        assert r['severe'] is True

    def test_6m_moderate(self):
        r = logic.interpret_weight_loss_glim(None, 15.0)
        assert r['present'] is True
        assert r['severe'] is False

    def test_6m_severe(self):
        r = logic.interpret_weight_loss_glim(None, 21.0)
        assert r['present'] is True
        assert r['severe'] is True

    def test_no_loss_below_threshold(self):
        r = logic.interpret_weight_loss_glim(3.0, 5.0)
        assert r['present'] is False

    def test_3m_boundary_exact_5(self):
        # >5 means 5.0 itself is NOT present
        r = logic.interpret_weight_loss_glim(5.0, None)
        assert r['present'] is False

    def test_3m_just_above_5(self):
        r = logic.interpret_weight_loss_glim(5.1, None)
        assert r['present'] is True


# ──────────────────────────────────────────────
# auto_estimate_mna_q_b
# ──────────────────────────────────────────────

class TestAutoEstimateMnaQB:
    def test_no_loss(self):
        assert logic.auto_estimate_mna_q_b(60, 60) == 3

    def test_less_than_3kg(self):
        assert logic.auto_estimate_mna_q_b(58, 60) == 2

    def test_exactly_3kg(self):
        assert logic.auto_estimate_mna_q_b(57, 60) == 0

    def test_more_than_3kg(self):
        assert logic.auto_estimate_mna_q_b(55, 60) == 0

    def test_weight_gain(self):
        # gain → loss = negative → returns 3
        assert logic.auto_estimate_mna_q_b(62, 60) == 3

    def test_none_current(self):
        assert logic.auto_estimate_mna_q_b(None, 60) is None

    def test_none_previous(self):
        assert logic.auto_estimate_mna_q_b(60, None) is None


# ──────────────────────────────────────────────
# auto_estimate_mna_q_f_bmi
# ──────────────────────────────────────────────

class TestAutoEstimateMnaQFBmi:
    def test_below_19(self):
        assert logic.auto_estimate_mna_q_f_bmi(18.5) == 0

    def test_19_to_21(self):
        assert logic.auto_estimate_mna_q_f_bmi(20.0) == 1

    def test_21_to_23(self):
        assert logic.auto_estimate_mna_q_f_bmi(22.0) == 2

    def test_above_23(self):
        assert logic.auto_estimate_mna_q_f_bmi(25.0) == 3

    def test_exactly_19(self):
        assert logic.auto_estimate_mna_q_f_bmi(19.0) == 1

    def test_exactly_21(self):
        assert logic.auto_estimate_mna_q_f_bmi(21.0) == 2

    def test_exactly_23(self):
        assert logic.auto_estimate_mna_q_f_bmi(23.0) == 3

    def test_none(self):
        assert logic.auto_estimate_mna_q_f_bmi(None) is None


# ──────────────────────────────────────────────
# auto_estimate_mna_q_f_cc
# ──────────────────────────────────────────────

class TestAutoEstimateMnaQFCc:
    def test_below_31(self):
        assert logic.auto_estimate_mna_q_f_cc(30.9) == 0

    def test_exactly_31(self):
        assert logic.auto_estimate_mna_q_f_cc(31.0) == 3

    def test_above_31(self):
        assert logic.auto_estimate_mna_q_f_cc(35.0) == 3

    def test_none(self):
        assert logic.auto_estimate_mna_q_f_cc(None) is None


# ──────────────────────────────────────────────
# calc_glim_severity
# ──────────────────────────────────────────────

def _glim(**kwargs):
    """Helper with sensible defaults for calc_glim_severity."""
    defaults = dict(
        glim_weight_loss=False,
        glim_low_bmi=False,
        glim_muscle='none',
        glim_intake=False,
        glim_inflam=False,
        glim_chronic=False,
        age=65,
        bmi=None,
        wl_pct_3m=None,
        wl_pct_6m=None,
    )
    defaults.update(kwargs)
    return logic.calc_glim_severity(**defaults)


class TestCalcGlimSeverity:
    def test_no_criteria(self):
        r = _glim()
        assert r['diagnosed'] is False

    def test_phenotypic_only(self):
        r = _glim(glim_weight_loss=True)
        assert r['diagnosed'] is False
        assert r['phenotypic_met'] is True
        assert r['etiologic_met'] is False

    def test_etiologic_only(self):
        r = _glim(glim_intake=True)
        assert r['diagnosed'] is False
        assert r['phenotypic_met'] is False

    def test_stage1_weight_loss(self):
        r = _glim(glim_weight_loss=True, glim_intake=True, wl_pct_3m=7.0)
        assert r['diagnosed'] is True
        assert r['severity'] == 'stage1'

    def test_stage2_weight_loss_3m(self):
        r = _glim(glim_weight_loss=True, glim_intake=True, wl_pct_3m=12.0)
        assert r['diagnosed'] is True
        assert r['severity'] == 'stage2'

    def test_stage2_weight_loss_6m(self):
        r = _glim(glim_weight_loss=True, glim_intake=True, wl_pct_6m=22.0)
        assert r['diagnosed'] is True
        assert r['severity'] == 'stage2'

    def test_stage1_low_bmi_young(self):
        r = _glim(glim_low_bmi=True, glim_inflam=True, age=60, bmi=19.5)
        assert r['diagnosed'] is True
        assert r['severity'] == 'stage1'

    def test_stage2_low_bmi_young(self):
        r = _glim(glim_low_bmi=True, glim_inflam=True, age=60, bmi=18.0)
        assert r['diagnosed'] is True
        assert r['severity'] == 'stage2'

    def test_stage1_muscle_mild(self):
        r = _glim(glim_muscle='mild', glim_chronic=True)
        assert r['diagnosed'] is True
        assert r['severity'] == 'stage1'

    def test_stage2_muscle_severe(self):
        r = _glim(glim_muscle='severe', glim_chronic=True)
        assert r['diagnosed'] is True
        assert r['severity'] == 'stage2'

    def test_phenotypic_items_listed(self):
        r = _glim(glim_weight_loss=True, glim_low_bmi=True, glim_intake=True)
        assert '体重減少' in r['phenotypic_items']
        assert '低BMI' in r['phenotypic_items']

    def test_etiologic_items_listed(self):
        r = _glim(glim_weight_loss=True, glim_intake=True, glim_inflam=True, glim_chronic=True)
        assert len(r['etiologic_items']) == 3


# ──────────────────────────────────────────────
# get_recommendations
# ──────────────────────────────────────────────

class TestGetRecommendations:
    def test_normal(self):
        recs = logic.get_recommendations('normal', None, None)
        assert len(recs) == 1
        assert '6ヶ月' in recs[0]

    def test_risk_no_glim(self):
        recs = logic.get_recommendations('risk', False, None)
        assert len(recs) == 2

    def test_stage1(self):
        recs = logic.get_recommendations('severe', True, 'stage1')
        assert any('Stage 1' in r for r in recs)

    def test_stage2(self):
        recs = logic.get_recommendations('severe', True, 'stage2')
        assert any('Stage 2' in r for r in recs)
        assert len(recs) == 3
