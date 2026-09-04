"""
Payme Merchant API integratsiyasi.
Hujjat: https://developer.help.paycom.uz/

Ishlash tartibi:
1. Biz `generate_checkout_url()` orqali foydalanuvchini Payme checkout sahifasiga yo'naltiramiz
   (booking_id va summani base64 qilib URL ichiga qo'shamiz).
2. Payme serveri to'lov holatlarida bizning `/api/v1/payments/payme/webhook` manzilimizga
   JSON-RPC so'rovlar yuboradi: CheckPerformTransaction, CreateTransaction,
   PerformTransaction, CancelTransaction, CheckTransaction.
3. Har bir so'rovni quyidagi funksiyalar qayta ishlaydi va Payme kutayotgan formatda javob beradi.

DIQQAT: bu ishlaydigan integratsiya skeleti. Production uchun Payme "sandbox"da
to'liq test qilib, xatolik kodlarini aniq moslashtirish tavsiya etiladi.
"""
import base64
import time
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import booking as booking_crud, payment as payment_crud
from app.models.booking import BookingStatus
from app.models.payment import Payment, PaymentProvider, PaymentStatus

PAYME_CHECKOUT_BASE = "https://checkout.paycom.uz"


class PaymeError:
    INVALID_AMOUNT = -31001
    TRANSACTION_NOT_FOUND = -31003
    COULD_NOT_PERFORM = -31008
    COULD_NOT_CANCEL = -31007
    ACCOUNT_NOT_FOUND = -31050
    ORDER_ALREADY_PAID = -31051


def generate_checkout_url(booking_id: str, amount_uzs: Decimal) -> str:
    """Payme summani tiyin(=1/100 so'm)da kutadi."""
    amount_tiyin = int(Decimal(amount_uzs) * 100)
    params = (
        f"m={settings.PAYME_MERCHANT_ID};"
        f"ac.{settings.PAYME_ACCOUNT_FIELD}={booking_id};"
        f"a={amount_tiyin}"
    )
    encoded = base64.b64encode(params.encode()).decode()
    return f"{PAYME_CHECKOUT_BASE}/{encoded}"


def _find_payment_for_account(db: Session, account: dict) -> Payment | None:
    booking_id = account.get(settings.PAYME_ACCOUNT_FIELD)
    if not booking_id:
        return None
    booking = booking_crud.get_by_id(db, booking_id)
    if not booking:
        return None
    return payment_crud.get_by_booking_id(db, booking.id)


def check_perform_transaction(db: Session, params: dict) -> dict:
    payment = _find_payment_for_account(db, params.get("account", {}))
    if not payment:
        return {"error": {"code": PaymeError.ACCOUNT_NOT_FOUND, "message": "Booking topilmadi"}}

    expected_tiyin = int(Decimal(payment.amount) * 100)
    if int(params.get("amount", 0)) != expected_tiyin:
        return {"error": {"code": PaymeError.INVALID_AMOUNT, "message": "Summa mos kelmadi"}}

    if payment.status == PaymentStatus.performed:
        return {"error": {"code": PaymeError.ORDER_ALREADY_PAID, "message": "Allaqachon to'langan"}}

    return {"result": {"allow": True}}


def create_transaction(db: Session, params: dict) -> dict:
    payment = _find_payment_for_account(db, params.get("account", {}))
    if not payment:
        return {"error": {"code": PaymeError.ACCOUNT_NOT_FOUND, "message": "Booking topilmadi"}}

    payme_trans_id = params["id"]

    # Agar bu tranzaksiya avval yaratilgan bo'lsa - holatini qaytaramiz (idempotent)
    if payment.provider_transaction_id == payme_trans_id:
        return {
            "result": {
                "create_time": int(payment.created_at.timestamp() * 1000),
                "transaction": payme_trans_id,
                "state": 1,
            }
        }

    payment.provider = PaymentProvider.payme
    payment.provider_transaction_id = payme_trans_id
    payment.status = PaymentStatus.created
    db.commit()

    return {
        "result": {
            "create_time": int(time.time() * 1000),
            "transaction": payme_trans_id,
            "state": 1,
        }
    }


def perform_transaction(db: Session, params: dict) -> dict:
    payment = payment_crud.get_by_transaction_id(db, PaymentProvider.payme, params["id"])
    if not payment:
        return {"error": {"code": PaymeError.TRANSACTION_NOT_FOUND, "message": "Tranzaksiya topilmadi"}}

    if payment.status != PaymentStatus.performed:
        payment_crud.mark_performed(db, payment)
        booking = booking_crud.get_by_id(db, payment.booking_id)
        booking_crud.update_status(db, booking, BookingStatus.confirmed)

    return {
        "result": {
            "transaction": params["id"],
            "perform_time": int(payment.performed_at.timestamp() * 1000),
            "state": 2,
        }
    }


def cancel_transaction(db: Session, params: dict) -> dict:
    payment = payment_crud.get_by_transaction_id(db, PaymentProvider.payme, params["id"])
    if not payment:
        return {"error": {"code": PaymeError.TRANSACTION_NOT_FOUND, "message": "Tranzaksiya topilmadi"}}

    payment_crud.mark_cancelled(db, payment, reason=f"Payme reason={params.get('reason')}")
    booking = booking_crud.get_by_id(db, payment.booking_id)
    booking_crud.update_status(db, booking, BookingStatus.cancelled)

    return {
        "result": {
            "transaction": params["id"],
            "cancel_time": int(payment.cancelled_at.timestamp() * 1000),
            "state": -1,
        }
    }


def check_transaction(db: Session, params: dict) -> dict:
    payment = payment_crud.get_by_transaction_id(db, PaymentProvider.payme, params["id"])
    if not payment:
        return {"error": {"code": PaymeError.TRANSACTION_NOT_FOUND, "message": "Tranzaksiya topilmadi"}}

    state = {"created": 1, "performed": 2, "cancelled": -1}[payment.status.value]
    return {
        "result": {
            "create_time": int(payment.created_at.timestamp() * 1000),
            "perform_time": int(payment.performed_at.timestamp() * 1000) if payment.performed_at else 0,
            "cancel_time": int(payment.cancelled_at.timestamp() * 1000) if payment.cancelled_at else 0,
            "transaction": params["id"],
            "state": state,
            "reason": None,
        }
    }


METHOD_HANDLERS = {
    "CheckPerformTransaction": check_perform_transaction,
    "CreateTransaction": create_transaction,
    "PerformTransaction": perform_transaction,
    "CancelTransaction": cancel_transaction,
    "CheckTransaction": check_transaction,
}
