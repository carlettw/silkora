from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class Country(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "countries"

    name: Mapped[dict] = mapped_column(JSONB)  # {"uz": "O'zbekiston", "ru": "...", "en": "Uzbekistan"}
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    cover_image: Mapped[str | None] = mapped_column(String(500), nullable=True)

    destinations: Mapped[list["Destination"]] = relationship(back_populates="country")


class Destination(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "destinations"

    name: Mapped[dict] = mapped_column(JSONB)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cover_image: Mapped[str | None] = mapped_column(String(500), nullable=True)

    country_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("countries.id"))
    country: Mapped["Country"] = relationship(back_populates="destinations")
