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
