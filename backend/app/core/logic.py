"""純粋関数群 — Qtなし（HTMLから移植）"""
from __future__ import annotations
from typing import Optional


# ──────────────────────────────────────────────
# 基本計算
# ──────────────────────────────────────────────

def calc_bmi(weight: Optional[float], height: Optional[float]) -> Optional[float]:
    """BMI = weight(kg) / (height(m))²"""
    if not weight or not height or height <= 0:
        return None
    return weight / ((height / 100) ** 2)


def calc_weight_loss_pct(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    """体重減少率 = (previous - current) / previous × 100"""
    if not current or not previous or previous <= 0:
        return None
    return ((previous - current) / previous) * 100


# ──────────────────────────────────────────────
# GLIM BMI 判定
# ──────────────────────────────────────────────

def is_low_bmi_glim(bmi: Optional[float], age: int) -> bool:
    """アジア人 GLIM 基準: 70歳以上 <22、70歳未満 <20"""
    if bmi is None:
        return False
    return bmi < 22 if age >= 70 else bmi < 20


def is_low_bmi_severe(bmi: Optional[float], age: int) -> bool:
    """GLIM Stage-2 BMI 基準: 70歳以上 <20、70歳未満 <18.5"""
    if bmi is None:
        return False
    return bmi < 20 if age >= 70 else bmi < 18.5


# ──────────────────────────────────────────────
# MNA-SF
# ──────────────────────────────────────────────

def interpret_mna_sf_score(total: Optional[int]) -> dict:
    """
    Returns:
        category: 'normal' | 'risk' | 'severe'
        label: 日本語ラベル
        color_key: 'normal' | 'risk' | 'mal'  (color palette key)
    """
    if total is None:
        return {"category": "unknown", "label": "未入力", "color_key": "muted"}
    if total >= 12:
        return {"category": "normal", "label": "栄養良好", "color_key": "normal"}
    if total >= 8:
        return {"category": "risk", "label": "低栄養のリスクあり", "color_key": "risk"}
    return {"category": "severe", "label": "低栄養の可能性", "color_key": "mal"}


# ──────────────────────────────────────────────
# GLIM 体重減少 解釈
# ──────────────────────────────────────────────

def interpret_weight_loss_glim(
    pct_3m: Optional[float],
    pct_6m: Optional[float],
) -> dict:
    """
    Returns:
        present: bool
        severe: bool
        detail: str
    """
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


# ──────────────────────────────────────────────
# GLIM 重症度判定
# ──────────────────────────────────────────────

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
    """
    Returns:
        diagnosed: bool
        severity: None | 'stage1' | 'stage2'
        reasons: list[str]
        phenotypic_met: bool
        etiologic_met: bool
        phenotypic_items: list[str]
        etiologic_items: list[str]
    """
    phenotypic_met = glim_weight_loss or glim_low_bmi or glim_muscle != "none"
    etiologic_met = glim_intake or glim_inflam or glim_chronic
    diagnosed = phenotypic_met and etiologic_met

    phenotypic_items: list = []
    etiologic_items: list = []
    reasons: list = []

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

    # 体重減少
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

    # BMI
    if glim_low_bmi and bmi is not None:
        if is_low_bmi_severe(bmi, age):
            stage2 = True
            reasons.append(f"BMI {bmi:.1f} — 高度低BMI（Stage 2: 70歳未満<18.5 / 70歳以上<20）")
        else:
            reasons.append(f"BMI {bmi:.1f} — 低BMI（Stage 1: 70歳未満<20 / 70歳以上<22）")
    elif glim_low_bmi:
        reasons.append("低BMIあり（臨床判断、BMI計算不可）")

    # 筋肉量
    if glim_muscle == "severe":
        stage2 = True
        reasons.append("筋肉量の高度低下（Stage 2基準）")
    elif glim_muscle == "mild":
        reasons.append("筋肉量の軽〜中等度低下（Stage 1基準）")

    # 病因
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


# ──────────────────────────────────────────────
# MNA-SF 自動推定
# ──────────────────────────────────────────────

def auto_estimate_mna_q_b(
    weight_kg: Optional[float],
    weight_3m_kg: Optional[float],
) -> Optional[int]:
    """
    Q-B 自動推定（3ヶ月体重減少）
    Returns: 0 = 3kg以上減少, 1 = 不明, 2 = 1〜3kg減少, 3 = 減少なし
    """
    if weight_kg is None or weight_3m_kg is None:
        return None
    loss = weight_3m_kg - weight_kg  # 正 = 減少
    if loss >= 3:
        return 0
    if loss > 0:
        return 2
    return 3


def auto_estimate_mna_q_f_bmi(bmi: Optional[float]) -> Optional[int]:
    """
    Q-F BMI 自動推定
    Returns: 0=<19, 1=19-21, 2=21-23, 3=>=23
    """
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
    """
    Q-F CC 自動推定
    Returns: 0=<31cm, 3=>=31cm
    """
    if cc_cm is None:
        return None
    return 3 if cc_cm >= 31 else 0
