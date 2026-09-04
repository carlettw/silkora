import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentProvider, PaymentStatus
from app.models.booking import Booking


def get_or_create(db: Session, booking: Booking, provider: PaymentProvider) -> Payment:
    existing = db.execute(select(Payment).where(Payment.booking_id == booking.id)).scalar_one_or_none()
    if existing:
        existing.provider = provider
        existing.status = PaymentStatus.created
        db.commit()
        db.refresh(existing)
        return existing

    payment = Payment(
        booking_id=booking.id,
        provider=provider,
        amount=booking.total_price,
        currency=booking.currency,
        status=PaymentStatus.created,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def get_by_transaction_id(db: Session, provider: PaymentProvider, transaction_id: str) -> Payment | None:
    return db.execute(
        select(Payment).where(Payment.provider == provider, Payment.provider_transaction_id == transaction_id)
    ).scalar_one_or_none()


def get_by_booking_id(db: Session, booking_id: uuid.UUID) -> Payment | None:
    return db.execute(select(Payment).where(Payment.booking_id == booking_id)).scalar_one_or_none()


def mark_performed(db: Session, payment: Payment) -> Payment:
    payment.status = PaymentStatus.performed
    payment.performed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(payment)
    return payment


def mark_cancelled(db: Session, payment: Payment, reason: str | None = None) -> Payment:
    payment.status = PaymentStatus.cancelled
    payment.cancelled_at = datetime.now(timezone.utc)
    payment.cancel_reason = reason
    db.commit()
    db.refresh(payment)
    return payment
