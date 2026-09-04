# ============================================================
# Centralia Backend - Avtomatik yangilash skripti
# Ishlatish: shu faylni loyiha papkasiga (centralia-backend) qo'ying
# va PowerShell'da: .\update_backend.ps1
# ============================================================

$ErrorActionPreference = "Stop"

# .NET va PowerShell "joriy papka" tushunchasi har xil bo'lishi mumkin - shuni tenglashtiramiz
[System.IO.Directory]::SetCurrentDirectory((Get-Location).Path)
$ProjectRoot = (Get-Location).Path

Write-Host "1) Loyiha papkasida ekanligingizni tekshiryapmiz..." -ForegroundColor Cyan
if (-not (Test-Path (Join-Path $ProjectRoot "app\main.py"))) {
    Write-Host "XATO: Bu skriptni centralia-backend papkasi ichida ishga tushiring!" -ForegroundColor Red
    exit 1
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    $FullPath = Join-Path $ProjectRoot $Path
    $dir = Split-Path -Path $FullPath -Parent
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($FullPath, $Content, $utf8NoBom)
}

Write-Host "2) Fayllarni yangilaymiz..." -ForegroundColor Cyan

Write-Utf8NoBom -Path "app\models\site_stats.py" -Content @'
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class SiteStats(UUIDPKMixin, TimestampMixin, Base):
    """
    Bosh sahifadagi statistika bloki uchun bitta (singleton) qator.
    Masalan: '12 yillik tajriba', '95% mijozlar mamnunligi' va h.k.
    Admin panel orqali tahrirlanadi, frontend GET /site-stats bilan oladi.
    """
    __tablename__ = "site_stats"

    years_experience: Mapped[int] = mapped_column(Integer, default=0)
    satisfaction_percent: Mapped[int] = mapped_column(Integer, default=0)
    completed_trips: Mapped[int] = mapped_column(Integer, default=0)
    happy_travelers: Mapped[int] = mapped_column(Integer, default=0)

'@
Write-Host "  - app\models\site_stats.py yangilandi" -ForegroundColor Green

Write-Utf8NoBom -Path "app\models	our.py" -Content @'
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

    tour: Mapped["Tour"] = relationship(back_populates="itinerary")

'@
Write-Host "  - app\models	our.py yangilandi" -ForegroundColor Green

Write-Utf8NoBom -Path "app\models\__init__.py" -Content @'
from app.models.user import User, UserRole
from app.models.geo import Country, Destination
from app.models.tour import Tour, TourImage, TourItineraryDay, TourCategory, tour_countries, tour_destinations
from app.models.content import Review, Blog
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentProvider, PaymentStatus
from app.models.site_stats import SiteStats

__all__ = [
    "User", "UserRole",
    "Country", "Destination",
    "Tour", "TourImage", "TourItineraryDay", "TourCategory", "tour_countries", "tour_destinations",
    "Review", "Blog",
    "Booking", "BookingStatus",
    "Payment", "PaymentProvider", "PaymentStatus",
    "SiteStats",
]

'@
Write-Host "  - app\models\__init__.py yangilandi" -ForegroundColor Green

Write-Utf8NoBom -Path "appimport uuid

from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.models.tour import Tour, TourItineraryDay, TourCategory
from app.models.geo import Country, Destination
from app.schemas.tour import TourCreate, TourUpdate


def _base_query():
    return select(Tour).options(
        selectinload(Tour.countries),
        selectinload(Tour.destinations),
        selectinload(Tour.images),
        selectinload(Tour.itinerary),
        selectinload(Tour.reviews),
    )


def get_by_slug(db: Session, slug: str) -> Tour | None:
    return db.execute(_base_query().where(Tour.slug == slug)).scalar_one_or_none()


def get_by_id(db: Session, tour_id: uuid.UUID) -> Tour | None:
    return db.execute(_base_query().where(Tour.id == tour_id)).scalar_one_or_none()


def list_tours(
    db: Session,
    page: int = 1,
    page_size: int = 12,
    country_slug: str | None = None,
    destination_slug: str | None = None,
    category: TourCategory | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    search: str | None = None,
    featured: bool | None = None,
) -> tuple[list[Tour], int]:
    query = _base_query().where(Tour.is_active == True)  # noqa: E712

    if country_slug:
        query = query.join(Tour.countries).where(Country.slug == country_slug)
    if destination_slug:
        query = query.join(Tour.destinations).where(Destination.slug == destination_slug)
    if category:
        query = query.where(Tour.category == category)
    if min_price is not None:
        query = query.where(Tour.price >= min_price)
    if max_price is not None:
        query = query.where(Tour.price <= max_price)
    if featured is not None:
        query = query.where(Tour.is_featured == featured)
    if search:
        # JSONB matnida sodda qidiruv (uz/ru/en barcha kalitlar bo'ylab)
        query = query.where(func.cast(Tour.title, __import__("sqlalchemy").String).ilike(f"%{search}%"))

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    items = list(db.execute(query).scalars().unique())
    return items, total


def create_tour(db: Session, data: TourCreate) -> Tour:
    tour = Tour(
        title=data.title,
        slug=data.slug,
        short_description=data.short_description,
        description=data.description,
        category=data.category,
        duration_days=data.duration_days,
        duration_nights=data.duration_nights,
        price=data.price,
        currency=data.currency,
        cover_image=data.cover_image,
        max_group_size=data.max_group_size,
        is_featured=data.is_featured,
    )
    if data.country_ids:
        tour.countries = db.query(Country).filter(Country.id.in_(data.country_ids)).all()
    if data.destination_ids:
        tour.destinations = db.query(Destination).filter(Destination.id.in_(data.destination_ids)).all()

    db.add(tour)
    db.flush()  # tour.id kerak bo'ladi itinerary uchun

    for day in data.itinerary:
        db.add(TourItineraryDay(tour_id=tour.id, day_number=day.day_number, title=day.title, description=day.description))

    db.commit()
    db.refresh(tour)
    return get_by_id(db, tour.id)


def update_tour(db: Session, tour: Tour, data: TourUpdate) -> Tour:
    update_data = data.model_dump(exclude_unset=True, exclude={"country_ids", "destination_ids"})
    for field, value in update_data.items():
        setattr(tour, field, value)

    if data.country_ids is not None:
        tour.countries = db.query(Country).filter(Country.id.in_(data.country_ids)).all()
    if data.destination_ids is not None:
        tour.destinations = db.query(Destination).filter(Destination.id.in_(data.destination_ids)).all()

    db.commit()
    db.refresh(tour)
    return get_by_id(db, tour.id)


def delete_tour(db: Session, tour: Tour) -> None:
    db.delete(tour)
    db.commit()

'@
Write-Host "  - app
Write-Utf8NoBom -Path "appimport uuid
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.geo import Country, Destination
from app.models.tour import Tour, tour_countries


def list_countries(db: Session) -> list[tuple[Country, int]]:
    """Har bir davlat uchun faol turlar sonini ham qaytaradi."""
    query = (
        select(Country, func.count(func.distinct(Tour.id)).label("tour_count"))
        .outerjoin(tour_countries, tour_countries.c.country_id == Country.id)
        .outerjoin(Tour, (Tour.id == tour_countries.c.tour_id) & (Tour.is_active == True))  # noqa: E712
        .group_by(Country.id)
    )
    return list(db.execute(query).all())


def get_country_by_slug(db: Session, slug: str) -> Country | None:
    return db.execute(select(Country).where(Country.slug == slug)).scalar_one_or_none()


def create_country(db: Session, name: dict, slug: str, cover_image: str | None) -> Country:
    country = Country(name=name, slug=slug, cover_image=cover_image)
    db.add(country)
    db.commit()
    db.refresh(country)
    return country


def list_destinations(db: Session, country_slug: str | None = None) -> list[Destination]:
    query = select(Destination)
    if country_slug:
        query = query.join(Destination.country).where(Country.slug == country_slug)
    return list(db.execute(query).scalars())


def get_destination_by_slug(db: Session, slug: str) -> Destination | None:
    return db.execute(select(Destination).where(Destination.slug == slug)).scalar_one_or_none()


def create_destination(db: Session, data) -> Destination:
    destination = Destination(**data.model_dump())
    db.add(destination)
    db.commit()
    db.refresh(destination)
    return destination

'@
Write-Host "  - app
Write-Utf8NoBom -Path "app\schemas	our.py" -Content @'
import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.tour import TourCategory
from app.schemas.geo import CountryOut, DestinationOut


class TourImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    image_url: str
    order: int


class TourItineraryDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    day_number: int
    title: Any
    description: Any | None = None


class TourItineraryDayCreate(BaseModel):
    day_number: int
    title: dict
    description: dict | None = None


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
    images: list[TourImageOut] = []
    itinerary: list[TourItineraryDayOut] = []
    reviews: list[ReviewOut] = []


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

'@
Write-Host "  - app\schemas	our.py yangilandi" -ForegroundColor Green

Write-Utf8NoBom -Path "app\schemas\geo.py" -Content @'
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict


class CountryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: Any  # dict yoki lang= berilsa string
    slug: str
    cover_image: str | None = None
    tour_count: int = 0


class CountryCreate(BaseModel):
    name: dict
    slug: str
    cover_image: str | None = None


class DestinationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: Any
    slug: str
    description: Any | None = None
    cover_image: str | None = None
    country_id: uuid.UUID


class DestinationCreate(BaseModel):
    name: dict
    slug: str
    description: dict | None = None
    cover_image: str | None = None
    country_id: uuid.UUID

'@
Write-Host "  - app\schemas\geo.py yangilandi" -ForegroundColor Green

Write-Utf8NoBom -Path "apppi1ndpoints	ours.py" -Content @'
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.i18n import get_lang_param, localize
from app.api.deps import require_admin
from app.crud import tour as tour_crud
from app.models.tour import Tour, TourCategory
from app.schemas.common import Page
from app.schemas.tour import TourListItem, TourDetail, TourCreate, TourUpdate
from app.schemas.geo import CountryOut, DestinationOut

router = APIRouter(prefix="/tours", tags=["Tours"])


def _to_list_item(t: Tour, lang: str | None) -> TourListItem:
    return TourListItem(
        id=t.id, title=localize(t.title, lang), slug=t.slug, category=t.category,
        duration_days=t.duration_days, duration_nights=t.duration_nights,
        price=t.price, currency=t.currency, cover_image=t.cover_image, is_featured=t.is_featured,
        countries=[CountryOut(id=c.id, name=localize(c.name, lang), slug=c.slug, cover_image=c.cover_image) for c in t.countries],
    )


def _to_detail(t: Tour, lang: str | None) -> TourDetail:
    base = _to_list_item(t, lang)
    return TourDetail(
        **base.model_dump(),
        short_description=localize(t.short_description, lang),
        description=localize(t.description, lang),
        max_group_size=t.max_group_size,
        destinations=[
            DestinationOut(id=d.id, name=localize(d.name, lang), slug=d.slug,
                            description=localize(d.description, lang), cover_image=d.cover_image, country_id=d.country_id)
            for d in t.destinations
        ],
        images=[{"id": i.id, "image_url": i.image_url, "order": i.order} for i in sorted(t.images, key=lambda x: x.order)],
        itinerary=[
            {"id": day.id, "day_number": day.day_number, "title": localize(day.title, lang), "description": localize(day.description, lang)}
            for day in t.itinerary
        ],
        reviews=[
            {"id": r.id, "reviewer_name": r.reviewer_name, "reviewer_country": r.reviewer_country,
             "rating": r.rating, "text": r.text, "images": r.images or [], "is_verified": r.is_verified,
             "source": r.source, "source_url": r.source_url}
            for r in t.reviews if r.is_published
        ],
    )


@router.get("", response_model=Page[TourListItem])
def list_tours(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    country: str | None = None,
    destination: str | None = None,
    category: TourCategory | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    search: str | None = None,
    featured: bool | None = Query(None, description="true bo'lsa faqat 'Mashhur turlar' (is_featured) qaytadi"),
    lang: str | None = Depends(get_lang_param),
    db: Session = Depends(get_db),
):
    items, total = tour_crud.list_tours(
        db, page, page_size, country, destination, category, min_price, max_price, search, featured
    )
    return Page(
        items=[_to_list_item(t, lang) for t in items],
        total=total, page=page, page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/{slug}", response_model=TourDetail)
def get_tour(slug: str, lang: str | None = Depends(get_lang_param), db: Session = Depends(get_db)):
    tour = tour_crud.get_by_slug(db, slug)
    if not tour:
        raise HTTPException(status_code=404, detail="Tur topilmadi")
    return _to_detail(tour, lang)


@router.post("", response_model=TourDetail, dependencies=[Depends(require_admin)])
def create_tour(data: TourCreate, db: Session = Depends(get_db)):
    tour = tour_crud.create_tour(db, data)
    return _to_detail(tour, None)


@router.patch("/{tour_id}", response_model=TourDetail, dependencies=[Depends(require_admin)])
def update_tour(tour_id: uuid.UUID, data: TourUpdate, db: Session = Depends(get_db)):
    tour = tour_crud.get_by_id(db, tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tur topilmadi")
    tour = tour_crud.update_tour(db, tour, data)
    return _to_detail(tour, None)


@router.delete("/{tour_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_tour(tour_id: uuid.UUID, db: Session = Depends(get_db)):
    tour = tour_crud.get_by_id(db, tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tur topilmadi")
    tour_crud.delete_tour(db, tour)

'@
Write-Host "  - apppi1ndpoints	ours.py yangilandi" -ForegroundColor Green

Write-Utf8NoBom -Path "apppi1ndpoints\geo.py" -Content @'
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.i18n import get_lang_param, localize
from app.api.deps import require_admin
from app.crud import geo as geo_crud
from app.schemas.geo import CountryOut, CountryCreate, DestinationOut, DestinationCreate

router = APIRouter(tags=["Geography"])


@router.get("/countries", response_model=list[CountryOut])
def list_countries(lang: str | None = Depends(get_lang_param), db: Session = Depends(get_db)):
    countries = geo_crud.list_countries(db)
    result = []
    for c, tour_count in countries:
        result.append(CountryOut(id=c.id, name=localize(c.name, lang), slug=c.slug, cover_image=c.cover_image, tour_count=tour_count))
    return result


@router.post("/countries", response_model=CountryOut, dependencies=[Depends(require_admin)])
def create_country(data: CountryCreate, db: Session = Depends(get_db)):
    c = geo_crud.create_country(db, data.name, data.slug, data.cover_image)
    return CountryOut(id=c.id, name=c.name, slug=c.slug, cover_image=c.cover_image)


@router.get("/destinations", response_model=list[DestinationOut])
def list_destinations(
    country_slug: str | None = None,
    lang: str | None = Depends(get_lang_param),
    db: Session = Depends(get_db),
):
    destinations = geo_crud.list_destinations(db, country_slug)
    result = []
    for d in destinations:
        result.append(
            DestinationOut(
                id=d.id,
                name=localize(d.name, lang),
                slug=d.slug,
                description=localize(d.description, lang),
                cover_image=d.cover_image,
                country_id=d.country_id,
            )
        )
    return result


@router.post("/destinations", response_model=DestinationOut, dependencies=[Depends(require_admin)])
def create_destination(data: DestinationCreate, db: Session = Depends(get_db)):
    d = geo_crud.create_destination(db, data)
    return DestinationOut(
        id=d.id, name=d.name, slug=d.slug, description=d.description,
        cover_image=d.cover_image, country_id=d.country_id,
    )

'@
Write-Host "  - apppi1ndpoints\geo.py yangilandi" -ForegroundColor Green

Write-Utf8NoBom -Path "apppi1ndpoints\payments.py" -Content @'
import base64

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.api.deps import get_current_user
from app.crud import booking as booking_crud, payment as payment_crud
from app.models.payment import PaymentProvider
from app.models.user import User
from app.schemas.payment import PaymentInitRequest, PaymentInitResponse
from app.services import payme as payme_service
from app.services import click as click_service
from app.services import stripe_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/init", response_model=PaymentInitResponse)
def init_payment(
    data: PaymentInitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    To'lovni boshlash uchun LOGIN SHART. Frontend: 'To'lov qilish' tugmasi bosilganda
    agar foydalanuvchi login qilmagan bo'lsa, bu so'rov 401 qaytaradi - shu holatda
    login/ro'yxatdan o'tish oynasini ko'rsating, so'ng qayta chaqiring.
    Turlarni ko'rish (GET /tours, GET /tours/{slug}) esa login talab qilmaydi.
    """
    booking = booking_crud.get_by_id(db, data.booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")

    payment_crud.get_or_create(db, booking, data.provider)

    if data.provider == PaymentProvider.payme:
        url = payme_service.generate_checkout_url(str(booking.id), booking.total_price)
    elif data.provider == PaymentProvider.click:
        url = click_service.generate_checkout_url(str(booking.id), booking.total_price)
    elif data.provider == PaymentProvider.stripe:
        # Stripe odatda UZS'ni qo'llab-quvvatlamaydi - xalqaro to'lov uchun booking valyutasi
        # USD/EUR bo'lishi kerak. Agar UZS bo'lsa, frontend foydalanuvchini ogohlantirishi kerak.
        url = stripe_service.create_checkout_session(
            str(booking.id), booking.total_price, booking.currency, booking.booking_number
        )
    else:
        raise HTTPException(status_code=400, detail="Noma'lum to'lov tizimi")

    return PaymentInitResponse(
        payment_url=url, provider=data.provider, amount=booking.total_price, currency=booking.currency
    )


def _check_payme_auth(authorization: str | None):
    """Payme so'rovlari Basic Auth bilan keladi: login=Paycom, parol=PAYME_SECRET_KEY (yoki test key)."""
    if not authorization or not authorization.startswith("Basic "):
        raise HTTPException(status_code=401, detail="Ruxsat yo'q")
    try:
        decoded = base64.b64decode(authorization.split(" ", 1)[1]).decode()
        _, password = decoded.split(":", 1)
    except Exception:
        raise HTTPException(status_code=401, detail="Ruxsat yo'q")

    valid_keys = {settings.PAYME_SECRET_KEY, settings.PAYME_TEST_KEY}
    if password not in valid_keys:
        raise HTTPException(status_code=401, detail="Ruxsat yo'q")


@router.post("/payme/webhook")
async def payme_webhook(request: Request, db: Session = Depends(get_db), authorization: str | None = Header(None)):
    _check_payme_auth(authorization)
    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id")

    handler = payme_service.METHOD_HANDLERS.get(method)
    if not handler:
        return JSONResponse({"error": {"code": -32601, "message": "Method topilmadi"}, "id": request_id})

    result = handler(db, params)
    result["id"] = request_id
    return JSONResponse(result)


@router.post("/click/prepare")
async def click_prepare(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    return click_service.prepare(db, dict(form))


@router.post("/click/complete")
async def click_complete(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    return click_service.complete(db, dict(form))


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db), stripe_signature: str | None = Header(None)):
    payload = await request.body()
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Stripe-Signature header yo'q")
    result = stripe_service.handle_webhook_event(db, payload, stripe_signature)
    return JSONResponse(result)

'@
Write-Host "  - apppi1ndpoints\payments.py yangilandi" -ForegroundColor Green

Write-Utf8NoBom -Path "apppi1ndpoints\site_stats.py" -Content @'
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.api.deps import require_admin
from app.models.site_stats import SiteStats

router = APIRouter(prefix="/site-stats", tags=["Site Stats"])


class SiteStatsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    years_experience: int
    satisfaction_percent: int
    completed_trips: int
    happy_travelers: int


class SiteStatsUpdate(BaseModel):
    years_experience: int | None = None
    satisfaction_percent: int | None = None
    completed_trips: int | None = None
    happy_travelers: int | None = None


def _get_or_create(db: Session) -> SiteStats:
    stats = db.execute(select(SiteStats)).scalar_one_or_none()
    if not stats:
        stats = SiteStats(years_experience=0, satisfaction_percent=0, completed_trips=0, happy_travelers=0)
        db.add(stats)
        db.commit()
        db.refresh(stats)
    return stats


@router.get("", response_model=SiteStatsOut)
def get_site_stats(db: Session = Depends(get_db)):
    """Bosh sahifadagi statistika bloki uchun (login talab qilinmaydi)."""
    return _get_or_create(db)


@router.patch("", response_model=SiteStatsOut, dependencies=[Depends(require_admin)])
def update_site_stats(data: SiteStatsUpdate, db: Session = Depends(get_db)):
    """Statistika raqamlarini yangilash (faqat admin)."""
    stats = _get_or_create(db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(stats, field, value)
    db.commit()
    db.refresh(stats)
    return stats

'@
Write-Host "  - apppi1ndpoints\site_stats.py yangilandi" -ForegroundColor Green

Write-Utf8NoBom -Path "apppi1pi.py" -Content @'
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, tours, geo, bookings, payments, reviews, blogs, site_stats

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(geo.router)
api_router.include_router(tours.router)
api_router.include_router(bookings.router)
api_router.include_router(payments.router)
api_router.include_router(reviews.router)
api_router.include_router(blogs.router)
api_router.include_router(site_stats.router)

'@
Write-Host "  - apppi1pi.py yangilandi" -ForegroundColor Green

Write-Host "3) Kutubxonalarni tekshiryapmiz (agar venv faollashtirilgan bo'lsa)..." -ForegroundColor Cyan
pip install -r requirements.txt --quiet

Write-Host "4) Alembic migratsiya yaratyapmiz..." -ForegroundColor Cyan
alembic revision --autogenerate -m "add featured tours, site stats, tour_count"

Write-Host "5) Migratsiyani bazaga qo'llayapmiz..." -ForegroundColor Cyan
alembic upgrade head

Write-Host "6) Git orqali GitHub'ga yuklaymiz..." -ForegroundColor Cyan
git add .
git commit -m "Add featured tours, site stats, country tour_count, require login for payment init"
git push

Write-Host ""
Write-Host "TAYYOR! Render.com avtomatik ravishda yangi versiyani deploy qiladi (Auto-Deploy yoqilgan bo'lsa)." -ForegroundColor Yellow
Write-Host "Render dashboard'da 'Live' holatini kutib, so'ng sinab ko'ring." -ForegroundColor Yellow
