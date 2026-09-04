import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Numeric, ForeignKey, Enum, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class PaymentProvider(str, enum.Enum):
    payme = "payme"
    click = "click"
    stripe = "stripe"


class PaymentStatus(str, enum.Enum):
    created = "created"        # tranzaksiya yaratildi, hali to'lanmagan
    performed = "performed"    # muvaffaqiyatli to'landi
    cancelled = "cancelled"    # bekor qilindi (foydalanuvchi yoki xatolik sababli)


class Payment(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id"), unique=True)

    provider: Mapped[PaymentProvider] = mapped_column(Enum(PaymentProvider))
    # Payme uchun tranzaksiya ID matn (uzun raqam), Click uchun ham matn sifatida saqlaymiz
    provider_transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    click_trans_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="UZS")

    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.created)

    performed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    booking: Mapped["Booking"] = relationship(back_populates="payment")
