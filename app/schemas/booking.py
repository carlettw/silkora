import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, ConfigDict, Field, computed_field

from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    tour_id: uuid.UUID
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str
    tour_date: date
    num_adults: int = Field(default=1, ge=1)
    num_children: int = Field(default=0, ge=0)
    notes: str | None = None


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_number: str
    tour_id: uuid.UUID
    full_name: str
    email: EmailStr
    phone: str
    tour_date: date
    num_adults: int
    num_children: int
    total_price: Decimal
    currency: str
    status: BookingStatus
    notes: str | None = None
    created_at: datetime

    @computed_field
    @property
    def can_review(self) -> bool:
        """Frontendga: bu buyurtma uchun 'Izoh qoldirish' tugmasini ko'rsatish kerakmi."""
        return self.status == BookingStatus.completed


class BookingStatusUpdate(BaseModel):
    status: BookingStatus
