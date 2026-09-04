import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.payment import PaymentProvider, PaymentStatus


class PaymentInitRequest(BaseModel):
    booking_id: uuid.UUID
    provider: PaymentProvider


class PaymentInitResponse(BaseModel):
    """Frontend to'lov sahifasiga (Payme checkout / Click invoice) redirect qiladigan URL."""
    payment_url: str
    provider: PaymentProvider
    amount: Decimal
    currency: str


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_id: uuid.UUID
    provider: PaymentProvider
    status: PaymentStatus
    amount: Decimal
    currency: str
