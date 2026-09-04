import enum
import uuid
from datetime import date

from sqlalchemy import String, Integer, Numeric, ForeignKey, Enum, Date, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class BookingStatus(str, enum.Enum):
    pending = "pending"       # yaratilgan, to'lov kutilmoqda
    confirmed = "confirmed"   # to'langan / operator tasdiqladi
    cancelled = "cancelled"
    completed = "completed"   # tur tugagan


class Booking(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "bookings"

    booking_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)

    tour_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tours.id"))
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Mehmon sifatida ham buyurtma berish mumkin (user_id bo'sh bo'lishi mumkin)
    full_name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20))

    tour_date: Mapped[date] = mapped_column(Date)
    num_adults: Mapped[int] = mapped_column(Integer, default=1)
    num_children: Mapped[int] = mapped_column(Integer, default=0)

    total_price: Mapped[float] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.pending)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    tour: Mapped["Tour"] = relationship()
    payment: Mapped["Payment"] = relationship(back_populates="booking", uselist=False, cascade="all, delete-orphan")
