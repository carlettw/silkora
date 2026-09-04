import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class Review(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "reviews"

    tour_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tours.id", ondelete="CASCADE"))
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    reviewer_name: Mapped[str] = mapped_column(String(120))
    reviewer_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, default=5)
    text: Mapped[str] = mapped_column(Text)

    # Sayyoh yuklagan rasmlar URL manzillari ro'yxati: ["/media/reviews/xxx.jpg", ...]
    images: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True, default=list)

    source: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. "getyourguide", "site"
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Booking orqali tekshirilgan (haqiqatan sotib olgan) sharhmi
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    # Moderatsiyadan o'tguncha saytda ko'rinmasligi mumkin
    is_published: Mapped[bool] = mapped_column(default=True)

    tour: Mapped["Tour"] = relationship(back_populates="reviews")


class Blog(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "blogs"

    title: Mapped[dict] = mapped_column(JSONB)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    content: Mapped[dict] = mapped_column(JSONB)
    cover_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    read_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_published: Mapped[bool] = mapped_column(default=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
