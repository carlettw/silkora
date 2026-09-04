"""
Stripe Checkout integratsiyasi (xalqaro Visa/Mastercard/Amex kartalar uchun).
Hujjat: https://stripe.com/docs/checkout/quickstart

Ishlash tartibi:
1. `create_checkout_session()` Stripe'da to'lov sessiyasi yaratadi va foydalanuvchini
   Stripe'ning tayyor to'lov sahifasiga yo'naltiradigan URL qaytaradi.
2. Foydalanuvchi kartasini kiritib to'laydi (bu butunlay Stripe tomonida, biz karta
   ma'lumotlarini hech qachon ko'rmaymiz - PCI-DSS talablariga mos).
3. Stripe to'lov holatida bizning `/api/v1/payments/stripe/webhook` manzilimizga
   `checkout.session.completed` (muvaffaqiyatli) yoki boshqa hodisa yuboradi.
4. Webhook imzosi (`Stripe-Signature` header) orqali tekshiriladi - soxta so'rovlarning oldi olinadi.
"""
import stripe
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import booking as booking_crud, payment as payment_crud
from app.models.booking import BookingStatus
from app.models.payment import PaymentProvider, PaymentStatus

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(booking_id: str, amount: Decimal, currency: str, booking_number: str) -> str:
    """
    Stripe eng kichik pul birligida ishlaydi (masalan sentda, tiyinda emas):
    USD uchun *100, ko'pchilik valyutalar uchun ham shunday (UZS Stripe'da odatda
    qo'llab-quvvatlanmaydi - shuning uchun xalqaro to'lovlar uchun odatda USD ishlatiladi).
    """
    unit_amount = int(amount * 100)

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": currency.lower(),
                    "unit_amount": unit_amount,
                    "product_data": {"name": f"Centralia Tours - Booking {booking_number}"},
                },
                "quantity": 1,
            }
        ],
        client_reference_id=booking_id,
        metadata={"booking_id": booking_id},
        success_url=f"{settings.FRONTEND_SUCCESS_URL}?booking={booking_number}",
        cancel_url=f"{settings.FRONTEND_CANCEL_URL}?booking={booking_number}",
    )
    return session.url


def handle_webhook_event(db: Session, payload: bytes, sig_header: str) -> dict:
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return {"error": "Imzo noto'g'ri yoki payload buzilgan"}

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        booking_id = data.get("client_reference_id") or data.get("metadata", {}).get("booking_id")
        if not booking_id:
            return {"status": "ignored", "reason": "booking_id topilmadi"}

        booking = booking_crud.get_by_id(db, booking_id)
        if not booking:
            return {"status": "ignored", "reason": "booking topilmadi"}

        payment = payment_crud.get_or_create(db, booking, PaymentProvider.stripe)
        payment.provider_transaction_id = data.get("id")
        db.commit()

        if payment.status != PaymentStatus.performed:
            payment_crud.mark_performed(db, payment)
            booking_crud.update_status(db, booking, BookingStatus.confirmed)

        return {"status": "ok"}

    if event_type in ("checkout.session.expired", "payment_intent.payment_failed"):
        booking_id = data.get("client_reference_id") or data.get("metadata", {}).get("booking_id")
        if booking_id:
            booking = booking_crud.get_by_id(db, booking_id)
            payment = payment_crud.get_by_booking_id(db, booking.id) if booking else None
            if payment and payment.status != PaymentStatus.performed:
                payment_crud.mark_cancelled(db, payment, reason=f"Stripe event={event_type}")
                if booking:
                    booking_crud.update_status(db, booking, BookingStatus.cancelled)
        return {"status": "ok"}

    return {"status": "ignored", "reason": f"unhandled event {event_type}"}
