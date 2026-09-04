import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.uploads import save_upload_image
from app.api.deps import require_admin, get_current_user
from app.crud import booking as booking_crud, tour as tour_crud
from app.models.content import Review
from app.models.user import User
from app.schemas.tour import ReviewOut, ReviewCreate

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("", response_model=list[ReviewOut])
def list_reviews(tour_id: uuid.UUID | None = None, db: Session = Depends(get_db)):
    query = select(Review).where(Review.is_published == True)  # noqa: E712
    if tour_id:
        query = query.where(Review.tour_id == tour_id)
    return list(db.execute(query).scalars())


@router.post("", response_model=ReviewOut, status_code=201)
def create_review(
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Izoh faqat foydalanuvchi shu turni sotib olgan VA tur sanasi allaqachon
    o'tib bo'lgan holatda qoldirilishi mumkin (ya'ni sayohatdan keyin).
    Sotib olib, hali sayohat qilinmagan (kelajakdagi) buyurtma uchun ruxsat yo'q.
    Rasmlarni oldindan POST /reviews/upload-image orqali yuklab,
    qaytgan URLlarni `images` ro'yxatiga qo'shish kerak.
    """
    tour = tour_crud.get_by_id(db, data.tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tur topilmadi")

    booking = booking_crud.get_reviewable_booking(db, current_user.id, data.tour_id)
    if not booking:
        raise HTTPException(
            status_code=403,
            detail="Izoh faqat sotib olingan va allaqachon o'tib bo'lgan tur uchun qoldiriladi",
        )

    existing = db.execute(
        select(Review).where(Review.booking_id == booking.id)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Siz bu buyurtma uchun allaqachon izoh qoldirgansiz")

    review = Review(
        tour_id=data.tour_id,
        booking_id=booking.id,
        user_id=current_user.id,
        reviewer_name=current_user.full_name,
        reviewer_country=data.reviewer_country,
        rating=data.rating,
        text=data.text,
        images=data.images,
        source="site",
        is_verified=True,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.post("/upload-image")
async def upload_review_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Sayyoh izoh uchun rasm yuklaydi. Qaytgan URLni ReviewCreate.images ichiga qo'shing."""
    url = await save_upload_image(file, subfolder="reviews")
    return {"url": url}


@router.delete("/{review_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_review(review_id: uuid.UUID, db: Session = Depends(get_db)):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Sharh topilmadi")
    db.delete(review)
    db.commit()
