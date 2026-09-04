import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.tour import TourCategory
from app.schemas.geo import CountryOut, DestinationOut


class TourAccommodationOut(BaseModel):
    """Kunlik dasturdagi mehmonxona ma'lumoti (ixtiyoriy - masalan jo'nab ketish kunida bo'lmaydi)."""
    name: str | None = None
    stars: int | None = None
    address: str | None = None
    map_url: str | None = None
    check_in: str | None = None
    check_out: str | None = None
    rooms: Any | None = None  # {uz,ru,en} yoki lang= berilganda string
    photos: list[str] = []


class TourTransportationOut(BaseModel):
    type: str | None = None  # "driving" | "train" | "flight" | "walking"
    duration: str | None = None
    distance: str | None = None


class TourItineraryDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    day_number: int
    title: Any
    description: Any | None = None
    what_to_expect: Any | None = None  # {uz,ru,en} yoki lang= berilganda list[str]
    meals_included: list[str] = []
    transportation: TourTransportationOut | None = None
    gallery: list[str] = []
    accommodation: TourAccommodationOut | None = None


class TourItineraryDayCreate(BaseModel):
    day_number: int
    title: dict
    description: dict | None = None
    what_to_expect: dict | None = None
    meals_included: list[str] = []
    transportation: dict | None = None
    gallery: list[str] = []
    accommodation: dict | None = None


class TourFaqItem(BaseModel):
    """Bitta FAQ savol-javob. question/answer - {"uz": "...", "ru": "...", "en": "..."} yoki lang=
    berilganda string bo'lib qaytadi."""
    question: Any
    answer: Any


class TourPricingOptionOut(BaseModel):
    id: str
    type: str  # "group" | "private"
    label: Any  # {uz,ru,en} yoki lang= berilganda string
    price: Decimal
    currency: str
    min_people: int | None = None
    max_people: int | None = None


class TourPricingOptionCreate(BaseModel):
    id: str | None = None  # bo'sh qoldirilsa avtomatik generatsiya qilinadi
    type: str
    label: dict
    price: Decimal
    currency: str = "USD"
    min_people: int | None = None
    max_people: int | None = None


class RoutePointCreate(BaseModel):
    """Xarita/marshrut nuqtasi. type: 'start' | 'stop' | 'end'."""
    order: int
    type: str
    name: dict  # {"uz": "...", "ru": "...", "en": "..."}
    address: dict | None = None  # faqat start/end uchun to'liq manzil, {uz,ru,en}
    activity_type: str | None = None  # "photo_stop" | "guided_tour" | "shopping" (faqat "stop" uchun)
    duration_minutes: int | None = None
    has_extra_fee: bool | None = None
    latitude: float | None = None
    longitude: float | None = None


class RoutePointOut(BaseModel):
    order: int
    type: str
    name: Any  # dict yoki lang= berilganda string
    address: Any | None = None
    activity_type: str | None = None
    duration_minutes: int | None = None
    has_extra_fee: bool | None = None
    latitude: float | None = None
    longitude: float | None = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    reviewer_name: str
    reviewer_country: str | None
    rating: int
    text: str
    images: list[str] = []
    is_verified: bool = False
    source: str | None = None
    source_url: str | None = None


class ReviewCreate(BaseModel):
    tour_id: uuid.UUID
    rating: int = Field(default=5, ge=1, le=5)
    text: str = Field(min_length=3, max_length=3000)
    images: list[str] = Field(default_factory=list, max_length=10)
    reviewer_country: str | None = None


class TourListItem(BaseModel):
    """Tour ro'yxati (kartochka) uchun yengil sxema."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: Any
    slug: str
    category: TourCategory
    duration_days: int
    duration_nights: int
    price: Decimal
    currency: str
    cover_image: str | None
    is_featured: bool = False
    countries: list[CountryOut] = []


class TourDetail(TourListItem):
    short_description: Any | None = None
    description: Any | None = None
    max_group_size: int | None = None
    destinations: list[DestinationOut] = []
    images: list[str] = []
    itinerary: list[TourItineraryDayOut] = []
    reviews: list[ReviewOut] = []

    technical_level: int | None = None
    min_age: int | None = None
    fitness_level: int | None = None

    # dict[str, list[str]] (masalan {"uz": ["...", "..."]}) - yoki lang= berilganda list[str]
    highlights: dict[str, list[str]] | list[str] | None = None
    included: dict[str, list[str]] | list[str] | None = None
    excluded: dict[str, list[str]] | list[str] | None = None

    faqs: list[TourFaqItem] = []
    map_embed_url: str | None = None
    pricing_options: list[TourPricingOptionOut] = []
    route_points: list[RoutePointOut] = []


class TourCreate(BaseModel):
    title: dict
    slug: str
    short_description: dict | None = None
    description: dict | None = None
    category: TourCategory = TourCategory.multi_day
    duration_days: int
    duration_nights: int = 0
    price: Decimal
    currency: str = "USD"
    cover_image: str | None = None
    max_group_size: int | None = None
    is_featured: bool = False
    country_ids: list[uuid.UUID] = []
    destination_ids: list[uuid.UUID] = []
    itinerary: list[TourItineraryDayCreate] = []
    images: list[str] = []

    technical_level: int | None = None
    min_age: int | None = None
    fitness_level: int | None = None
    # {"uz": ["...", "..."], "ru": [...], "en": [...]} - har bir til uchun matnlar massivi
    highlights: dict[str, list[str]] | None = None
    included: dict[str, list[str]] | None = None
    excluded: dict[str, list[str]] | None = None
    faqs: list[dict] = []
    map_embed_url: str | None = None
    pricing_options: list[TourPricingOptionCreate] = []
    route_points: list[RoutePointCreate] = []


class TourUpdate(BaseModel):
    title: dict | None = None
    short_description: dict | None = None
    description: dict | None = None
    category: TourCategory | None = None
    duration_days: int | None = None
    duration_nights: int | None = None
    price: Decimal | None = None
    currency: str | None = None
    cover_image: str | None = None
    max_group_size: int | None = None
    is_active: bool | None = None
    is_featured: bool | None = None
    country_ids: list[uuid.UUID] | None = None
    destination_ids: list[uuid.UUID] | None = None
    images: list[str] | None = None
    itinerary: list[TourItineraryDayCreate] | None = None

    technical_level: int | None = None
    min_age: int | None = None
    fitness_level: int | None = None
    highlights: dict[str, list[str]] | None = None
    included: dict[str, list[str]] | None = None
    excluded: dict[str, list[str]] | None = None
    faqs: list[dict] | None = None
    map_embed_url: str | None = None
    pricing_options: list[TourPricingOptionCreate] | None = None
    route_points: list[RoutePointCreate] | None = None
