"""
Ko'p tillilik strategiyasi:
Har bir tarjima qilinadigan matn maydoni (title, description, ...) DBda
JSON ustun sifatida saqlanadi: {"uz": "...", "ru": "...", "en": "..."}

API javobida ikkita variant mavjud:
  - `?lang=uz` query param berilsa -> shu tildagi string qaytadi (frontend uchun qulay)
  - berilmasa -> barcha tillar bilan to'liq JSON obyekt qaytadi (admin panel uchun qulay)

Bu yondashuv alohida tarjima jadvallari yaratishdan ko'ra soddaroq va
ko'pchilik kichik/o'rta hajmdagi saytlar (masalan turizm agentligi) uchun yetarli.
"""
from typing import Optional

from fastapi import Query

from app.core.config import settings


def get_lang_param(
    lang: Optional[str] = Query(
        default=None,
        description="Javobni bitta tilga tekislash uchun: uz | ru | en. Berilmasa, barcha tillar qaytadi.",
    )
) -> Optional[str]:
    if lang and lang not in settings.SUPPORTED_LANGUAGES:
        lang = settings.DEFAULT_LANGUAGE
    return lang


def localize(value: dict | None, lang: Optional[str]) -> dict | str | None:
    """JSON tarjima maydonini so'ralgan tilga tekislaydi (yoki to'liq holda qaytaradi)."""
    if value is None:
        return None
    if not lang:
        return value
    return value.get(lang) or value.get(settings.DEFAULT_LANGUAGE) or next(iter(value.values()), "")


def validate_translations(value: dict) -> dict:
    """Kamida DEFAULT_LANGUAGE mavjudligini tekshiradi; yo'q tillarni bo'sh qoldiradi."""
    if settings.DEFAULT_LANGUAGE not in value or not value[settings.DEFAULT_LANGUAGE]:
        raise ValueError(f"'{settings.DEFAULT_LANGUAGE}' tilidagi matn majburiy")
    return {lang: value.get(lang, "") for lang in settings.SUPPORTED_LANGUAGES}
