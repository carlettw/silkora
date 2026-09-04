import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user_optional, get_current_user, require_admin
from app.crud import booking as booking_crud, tour as tour_crud
from app.models.user import User
from app.models.booking import BookingStatus
from app.schemas.booking import BookingCreate, BookingOut, BookingStatusUpdate

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", response_model=BookingOut, status_code=201)
def create_booking(
    data: BookingCreate,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    tour = tour_crud.get_by_id(db, data.tour_id)
    if not tour or not tour.is_active:
        raise HTTPException(status_code=404, detail="Tur topilmadi")

    booking = booking_crud.create_booking(db, data, tour, current_user.id if current_user else None)
    return booking


@router.get("/my", response_model=list[BookingOut])
def my_bookings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return booking_crud.list_for_user(db, current_user.id)


@router.get("/{booking_number}", response_model=BookingOut)
def get_booking(booking_number: str, db: Session = Depends(get_db)):
    booking = booking_crud.get_by_number(db, booking_number)
    if not booking:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    return booking


@router.get("", response_model=list[BookingOut], dependencies=[Depends(require_admin)])
def list_all_bookings(status: BookingStatus | None = None, db: Session = Depends(get_db)):
    return booking_crud.list_all(db, status)


@router.patch("/{booking_id}/status", response_model=BookingOut, dependencies=[Depends(require_admin)])
def update_booking_status(booking_id: uuid.UUID, data: BookingStatusUpdate, db: Session = Depends(get_db)):
    booking = booking_crud.get_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    return booking_crud.update_status(db, booking, data.status)


@router.post("/auto-complete", dependencies=[Depends(require_admin)])
def auto_complete_bookings(db: Session = Depends(get_db)):
    """Sanasi o'tgan barcha 'confirmed' buyurtmalarni 'completed'ga o'tkazadi (cron yoki admin tugmasi uchun)."""
    updated_count = booking_crud.auto_complete_past_bookings(db)
    return {"updated": updated_count}
