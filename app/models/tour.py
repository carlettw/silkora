import enum
import uuid

from sqlalchemy import String, Integer, Numeric, ForeignKey, Enum, Table, Column, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class TourCategory(str, enum.Enum):
    day_trip = "day_trip"
    multi_day = "multi_day"


tour_countries = Table(
    "tour_countries",
    Base.metadata,
    Column("tour_id", UUID(as_uuid=True), ForeignKey("tours.id", ondelete="CASCADE"), primary_key=True),
    Column("country_id", UUID(as_uuid=True), ForeignKey("countries.id", ondelete="CASCADE"), primary_key=True),
)

tour_destinations = Table(
    "tour_destinations",
    Base.metadata,
    Column("tour_id", UUID(as_uuid=True), ForeignKey("tours.id", ondelete="CASCADE"), primary_key=True),
    Column("destination_id", UUID(as_uuid=True), ForeignKey("destinations.id", ondelete="CASCADE"), primary_key=True),
)


class Tour(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "tours"

    title: Mapped[dict] = mapped_column(JSONB)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    short_description: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    description: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    category: Mapped[TourCategory] = mapped_column(Enum(TourCategory), default=TourCategory.multi_day)
    duration_days: Mapped[int] = mapped_column(Integer)
    duration_nights: Mapped[int] = mapped_column(Integer, default=0)

    price: Mapped[float] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    cover_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    max_group_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Tezkor ma'lumot bloki
    technical_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fitness_level: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Har biri {"uz": [...], "ru": [...], "en": [...]} shaklida (matnlar massivi)
    highlights: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    included: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    excluded: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # [{ "question": {uz,ru,en}, "answer": {uz,ru,en} }, ...]
    faqs: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    map_embed_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # [{ "id": "...", "type": "group"|"private", "label": {uz,ru,en}, "price": 489,
    #    "currency": "USD", "min_people": 2, "max_people": 6 }, ...]
    pricing_options: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # [{ "order": 1, "type": "start"|"stop"|"end", "name": {uz,ru,en}, "address": {uz,ru,en} (ixtiyoriy),
    #    "activity_type": "photo_stop"|"guided_tour"|"shopping" (ixtiyoriy, faqat "stop" uchun),
    #    "duration_minutes": 30 (ixtiyoriy), "has_extra_fee": true (ixtiyoriy),
    #    "latitude": 39.654, "longitude": 66.9749 }, ...]
    route_points: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    countries: Mapped[list["Country"]] = relationship(secondary=tour_countries)
    destinations: Mapped[list["Destination"]] = relationship(secondary=tour_destinations)

    images: Mapped[list["TourImage"]] = relationship(back_populates="tour", cascade="all, delete-orphan")
    itinerary: Mapped[list["TourItineraryDay"]] = relationship(
        back_populates="tour", cascade="all, delete-orphan", order_by="TourItineraryDay.day_number"
    )
    reviews: Mapped[list["Review"]] = relationship(back_populates="tour")


class TourImage(UUIDPKMixin, Base):
    __tablename__ = "tour_images"

    tour_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tours.id", ondelete="CASCADE"))
    image_url: Mapped[str] = mapped_column(String(500))
    order: Mapped[int] = mapped_column(Integer, default=0)

    tour: Mapped["Tour"] = relationship(back_populates="images")


class TourItineraryDay(UUIDPKMixin, Base):
    __tablename__ = "tour_itinerary_days"

    tour_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tours.id", ondelete="CASCADE"))
    day_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[dict] = mapped_column(JSONB)
    description: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # {"uz": [...], "ru": [...], "en": [...]}
    what_to_expect: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # ["breakfast", "lunch", "dinner"]
    meals_included: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # {"type": "driving"|"train"|"flight"|"walking", "duration": "1-2hrs", "distance": "5-8km"}
    transportation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # ["/media/itinerary/xxx.jpg", ...]
    gallery: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # {"name": "...", "stars": 3, "address": "...", "map_url": "...", "check_in": "14:00",
    #  "check_out": "14:00", "rooms": {uz,ru,en}, "photos": [...]}
    accommodation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    tour: Mapped["Tour"] = relationship(back_populates="itinerary")
