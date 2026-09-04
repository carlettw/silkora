import random
import string
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingStatus
from app.models.tour import Tour
from app.schemas.booking import BookingCreate


def _generate_booking_number() -> str:
    # Masalan: CT-7K3F91
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"CT-{suffix}"


def create_booking(db: Session, data: BookingCreate, tour: Tour, user_id: uuid.UUID | None) -> Booking:
    # Narxni serverda tur narxidan hisoblaymiz (frontenddan kelgan narxga ishonmaymiz)
    total = Decimal(tour.price) * (data.num_adults + data.num_children * Decimal("0.7"))
    total = total.quantize(Decimal("0.01"))

    booking = Booking(
        booking_number=_generate_booking_number(),
        tour_id=tour.id,
        user_id=user_id,
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        tour_date=data.tour_date,
        num_adults=data.num_adults,
        num_children=data.num_children,
        total_price=total,
        currency=tour.currency,
        notes=data.notes,
        status=BookingStatus.pending,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_by_id(db: Session, booking_id: uuid.UUID) -> Booking | None:
    return db.execute(select(Booking).where(Booking.id == booking_id)).scalar_one_or_none()


def get_by_number(db: Session, booking_number: str) -> Booking | None:
    return db.execute(select(Booking).where(Booking.booking_number == booking_number)).scalar_one_or_none()


def list_for_user(db: Session, user_id: uuid.UUID) -> list[Booking]:
    return list(db.execute(select(Booking).where(Booking.user_id == user_id).order_by(Booking.created_at.desc())).scalars())


def get_reviewable_booking(db: Session, user_id: uuid.UUID, tour_id: uuid.UUID) -> Booking | None:
    """
    Foydalanuvchi shu tur uchun izoh qoldirishi mumkinmi - FAQAT tur allaqachon
    o'tib bo'lgan (tour_date bugungidan oldin) buyurtma uchun ruxsat beriladi.
    `confirmed` holatdagi, sanasi o'tgan buyurtmalarni avtomatik `completed`ga o'tkazamiz.
    """
    candidates = list(
        db.execute(
            select(Booking).where(
                Booking.user_id == user_id,
                Booking.tour_id == tour_id,
                Booking.status.in_([BookingStatus.confirmed, BookingStatus.completed]),
            )
        ).scalars()
    )

    today = date.today()
    reviewable = None
    for booking in candidates:
        if booking.status == BookingStatus.confirmed and booking.tour_date < today:
            booking.status = BookingStatus.completed
            db.commit()
            db.refresh(booking)

        if booking.status == BookingStatus.completed and reviewable is None:
            reviewable = booking

    return reviewable


def list_all(db: Session, status: BookingStatus | None = None) -> list[Booking]:
    query = select(Booking).order_by(Booking.created_at.desc())
    if status:
        query = query.where(Booking.status == status)
    return list(db.execute(query).scalars())


def update_status(db: Session, booking: Booking, status: BookingStatus) -> Booking:
    booking.status = status
    db.commit()
    db.refresh(booking)
    return booking


def auto_complete_past_bookings(db: Session) -> int:
    """
    Tur sanasi o'tib ketgan, hali 'confirmed' turgan barcha buyurtmalarni
    'completed'ga o'tkazadi. Kunlik cron/scheduler orqali chaqirish tavsiya etiladi
    (masalan har kuni tunda), lekin admin panel tugmasi orqali ham chaqirish mumkin.
    Qaytadi: nechta buyurtma yangilangani.
    """
    today = date.today()
    past_bookings = list(
        db.execute(
            select(Booking).where(Booking.status == BookingStatus.confirmed, Booking.tour_date < today)
        ).scalars()
    )
    for booking in past_bookings:
        booking.status = BookingStatus.completed
    db.commit()
    return len(past_bookings)
