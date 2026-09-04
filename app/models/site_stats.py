from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class SiteStats(UUIDPKMixin, TimestampMixin, Base):
    """
    Bosh sahifadagi statistika bloki uchun bitta (singleton) qator.
    FAQAT 'years_experience' qo'lda (admin panel orqali) kiritiladi - qolgan
    raqamlar (satisfaction_percent, completed_trips, happy_travelers) haqiqiy
    buyurtma/sharh ma'lumotlaridan AVTOMATIK hisoblanadi (bu jadvalda saqlanmaydi,
    GET /site-stats so'ralganda jonli hisoblab beriladi).
    """
    __tablename__ = "site_stats"

    years_experience: Mapped[int] = mapped_column(Integer, default=0)
