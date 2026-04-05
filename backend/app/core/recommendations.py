"""Recommendation logic and Isocal 100 display decision."""
from __future__ import annotations
from typing import Optional


def get_recommendations(
    mna_category: Optional[str],
    glim_diagnosed: Optional[bool],
    glim_severity: Optional[str],
) -> list:
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
