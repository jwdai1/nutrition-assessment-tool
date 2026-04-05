"""Application configuration and Isocal 100 product data."""
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./nutrition_tool.db"
    cors_origins: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()

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
