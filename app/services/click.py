"""
Click Merchant API integratsiyasi.
Hujjat: https://docs.click.uz/

Ishlash tartibi:
1. `generate_checkout_url()` foydalanuvchini Click to'lov sahifasiga yo'naltiradi.
2. Click serveri to'lov bosqichlarida bizga ikkita so'rov yuboradi:
   - action=0 (Prepare): to'lovdan oldin tekshirish
   - action=1 (Complete): to'lov yakunlanganda tasdiqlash
   Har ikkalasi ham `sign_string` (md5 imzo) orqali tekshiriladi.
"""
import hashlib
from decimal import Decimal
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import booking as booking_crud, payment as payment_crud
from app.models.booking import BookingStatus
from app.models.payment import PaymentProvider, PaymentStatus

CLICK_CHECKOUT_BASE = "https://my.click.uz/services/pay"


class ClickError:
    SUCCESS = 0
    SIGN_CHECK_FAILED = -1
    INVALID_AMOUNT = -2
    ACTION_NOT_FOUND = -3
    ALREADY_PAID = -4
    USER_NOT_FOUND = -5
    TRANSACTION_NOT_FOUND = -6
    FAILED_TO_UPDATE = -7
    TRANSACTION_CANCELLED = -9


def generate_checkout_url(booking_id: str, amount_uzs: Decimal) -> str:
    params = {
        "service_id": settings.CLICK_SERVICE_ID,
        "merchant_id": settings.CLICK_MERCHANT_ID,
        "amount": str(amount_uzs),
        "transaction_param": booking_id,  # merchant_trans_id sifatida qaytadi
    }
    return f"{CLICK_CHECKOUT_BASE}?{urlencode(params)}"


def _verify_signature(data: dict, secret_key: str) -> bool:
    action = data.get("action")
    if action == "0":
        raw = (
            f"{data.get('click_trans_id')}{data.get('service_id')}{secret_key}"
            f"{data.get('merchant_trans_id')}{data.get('amount')}{data.get('action')}{data.get('sign_time')}"
        )
    else:
        raw = (
            f"{data.get('click_trans_id')}{data.get('service_id')}{secret_key}"
            f"{data.get('merchant_trans_id')}{data.get('merchant_prepare_id')}"
            f"{data.get('amount')}{data.get('action')}{data.get('sign_time')}"
        )
    expected = hashlib.md5(raw.encode()).hexdigest()
    return expected == data.get("sign_string")


def prepare(db: Session, data: dict) -> dict:
    if not _verify_signature(data, settings.CLICK_SECRET_KEY):
        return {"error": ClickError.SIGN_CHECK_FAILED, "error_note": "Imzo noto'g'ri"}

    booking = booking_crud.get_by_id(db, data.get("merchant_trans_id"))
    if not booking:
        return {"error": ClickError.USER_NOT_FOUND, "error_note": "Booking topilmadi"}

    if Decimal(str(data.get("amount"))) != Decimal(booking.total_price):
        return {"error": ClickError.INVALID_AMOUNT, "error_note": "Summa mos kelmadi"}

    payment = payment_crud.get_or_create(db, booking, PaymentProvider.click)
    payment.click_trans_id = int(data.get("click_trans_id"))
    db.commit()

    return {
        "click_trans_id": data.get("click_trans_id"),
        "merchant_trans_id": data.get("merchant_trans_id"),
        "merchant_prepare_id": str(payment.id),
        "error": ClickError.SUCCESS,
        "error_note": "OK",
    }


def complete(db: Session, data: dict) -> dict:
    if not _verify_signature(data, settings.CLICK_SECRET_KEY):
        return {"error": ClickError.SIGN_CHECK_FAILED, "error_note": "Imzo noto'g'ri"}

    booking = booking_crud.get_by_id(db, data.get("merchant_trans_id"))
    if not booking:
        return {"error": ClickError.USER_NOT_FOUND, "error_note": "Booking topilmadi"}

    payment = payment_crud.get_by_booking_id(db, booking.id)
    if not payment:
        return {"error": ClickError.TRANSACTION_NOT_FOUND, "error_note": "Tranzaksiya topilmadi"}

    error_code = int(data.get("error", 0))
    if error_code < 0:
        payment_crud.mark_cancelled(db, payment, reason=f"Click error={error_code}")
        booking_crud.update_status(db, booking, BookingStatus.cancelled)
        return {
            "click_trans_id": data.get("click_trans_id"),
            "merchant_trans_id": data.get("merchant_trans_id"),
            "merchant_confirm_id": str(payment.id),
            "error": ClickError.SUCCESS,
            "error_note": "OK",
        }

    if payment.status != PaymentStatus.performed:
        payment_crud.mark_performed(db, payment)
        booking_crud.update_status(db, booking, BookingStatus.confirmed)

    return {
        "click_trans_id": data.get("click_trans_id"),
        "merchant_trans_id": data.get("merchant_trans_id"),
        "merchant_confirm_id": str(payment.id),
        "error": ClickError.SUCCESS,
        "error_note": "OK",
    }
