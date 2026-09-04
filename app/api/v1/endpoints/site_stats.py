from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.api.deps import require_admin
from app.models.site_stats import SiteStats
from app.models.booking import Booking, BookingStatus
from app.models.content import Review

router = APIRouter(prefix="/site-stats", tags=["Site Stats"])


class SiteStatsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    years_experience: int
    satisfaction_percent: int
    completed_trips: int
    happy_travelers: int


class SiteStatsUpdate(BaseModel):
    """Faqat 'years_experience' qo'lda tahrirlanadi - qolganlari avtomatik hisoblanadi."""
    years_experience: int


def _get_or_create_singleton(db: Session) -> SiteStats:
    stats = db.execute(select(SiteStats)).scalar_one_or_none()
    if not stats:
        stats = SiteStats(years_experience=0)
        db.add(stats)
        db.commit()
        db.refresh(stats)
    return stats


def _compute_live_stats(db: Session) -> dict:
    """completed_trips, happy_travelers, satisfaction_percent - haqiqiy ma'lumotlardan hisoblanadi."""
    completed_trips = db.execute(
        select(func.count()).select_from(Booking).where(Booking.status == BookingStatus.completed)
    ).scalar_one()

    happy_travelers = db.execute(
        select(func.coalesce(func.sum(Booking.num_adults + Booking.num_children), 0))
        .where(Booking.status == BookingStatus.completed)
    ).scalar_one()

    avg_rating = db.execute(
        select(func.avg(Review.rating)).where(Review.is_published == True)  # noqa: E712
    ).scalar_one()
    satisfaction_percent = round((float(avg_rating) / 5) * 100) if avg_rating else 0

    return {
        "completed_trips": int(completed_trips),
        "happy_travelers": int(happy_travelers),
        "satisfaction_percent": satisfaction_percent,
    }


@router.get("", response_model=SiteStatsOut)
def get_site_stats(db: Session = Depends(get_db)):
    """
    Bosh sahifadagi statistika bloki (login talab qilinmaydi).
    'years_experience' - admin tomonidan qo'lda kiritilgan qiymat.
    Qolganlari - haqiqiy buyurtma/sharh ma'lumotlaridan jonli hisoblanadi.
    """
    stats = _get_or_create_singleton(db)
    live = _compute_live_stats(db)
    return SiteStatsOut(years_experience=stats.years_experience, **live)


@router.patch("", response_model=SiteStatsOut, dependencies=[Depends(require_admin)])
def update_site_stats(data: SiteStatsUpdate, db: Session = Depends(get_db)):
    """Faqat 'years_experience'ni yangilaydi (faqat admin)."""
    stats = _get_or_create_singleton(db)
    stats.years_experience = data.years_experience
    db.commit()
    db.refresh(stats)
    live = _compute_live_stats(db)
    return SiteStatsOut(years_experience=stats.years_experience, **live)
