import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.i18n import get_lang_param, localize
from app.api.deps import require_admin
from app.crud import tour as tour_crud
from app.models.tour import Tour, TourCategory
from app.schemas.common import Page
from app.schemas.tour import TourListItem, TourDetail, TourCreate, TourUpdate
from app.schemas.geo import CountryOut, DestinationOut

router = APIRouter(prefix="/tours", tags=["Tours"])


def _to_list_item(t: Tour, lang: str | None) -> TourListItem:
    return TourListItem(
        id=t.id, title=localize(t.title, lang), slug=t.slug, category=t.category,
        duration_days=t.duration_days, duration_nights=t.duration_nights,
        price=t.price, currency=t.currency, cover_image=t.cover_image, is_featured=t.is_featured,
        countries=[CountryOut(id=c.id, name=localize(c.name, lang), slug=c.slug, cover_image=c.cover_image) for c in t.countries],
    )


def _localize_faqs(faqs: list | None, lang: str | None) -> list[dict]:
    """faqs - [{"question": {uz,ru,en}, "answer": {uz,ru,en}}, ...] ro'yxatini tilga moslaydi."""
    if not faqs:
        return []
    return [
        {"question": localize(item.get("question"), lang), "answer": localize(item.get("answer"), lang)}
        for item in faqs
    ]


def _localize_pricing_options(options: list | None, lang: str | None) -> list[dict]:
    if not options:
        return []
    result = []
    for opt in options:
        opt = dict(opt)
        opt["label"] = localize(opt.get("label"), lang)
        result.append(opt)
    return result


def _localize_accommodation(accommodation: dict | None, lang: str | None) -> dict | None:
    if not accommodation:
        return None
    acc = dict(accommodation)
    if "rooms" in acc:
        acc["rooms"] = localize(acc.get("rooms"), lang)
    return acc


def _localize_route_points(points: list | None, lang: str | None) -> list[dict]:
    """route_points - [{"name": {uz,ru,en}, "address": {uz,ru,en}, ...}, ...] ro'yxatini tilga moslaydi."""
    if not points:
        return []
    result = []
    for p in points:
        p = dict(p)
        p["name"] = localize(p.get("name"), lang)
        if p.get("address"):
            p["address"] = localize(p.get("address"), lang)
        result.append(p)
    return sorted(result, key=lambda x: x.get("order", 0))


def _itinerary_day_to_dict(day, lang: str | None) -> dict:
    return {
        "id": day.id,
        "day_number": day.day_number,
        "title": localize(day.title, lang),
        "description": localize(day.description, lang),
        "what_to_expect": localize(day.what_to_expect, lang),
        "meals_included": day.meals_included or [],
        "transportation": day.transportation,
        "gallery": day.gallery or [],
        "accommodation": _localize_accommodation(day.accommodation, lang),
    }


def _to_detail(t: Tour, lang: str | None) -> TourDetail:
    base = _to_list_item(t, lang)
    return TourDetail(
        **base.model_dump(),
        short_description=localize(t.short_description, lang),
        description=localize(t.description, lang),
        max_group_size=t.max_group_size,
        destinations=[
            DestinationOut(id=d.id, name=localize(d.name, lang), slug=d.slug,
                            description=localize(d.description, lang), cover_image=d.cover_image, country_id=d.country_id)
            for d in t.destinations
        ],
        images=[i.image_url for i in sorted(t.images, key=lambda x: x.order)],
        itinerary=[_itinerary_day_to_dict(day, lang) for day in t.itinerary],
        reviews=[
            {"id": r.id, "reviewer_name": r.reviewer_name, "reviewer_country": r.reviewer_country,
             "rating": r.rating, "text": r.text, "images": r.images or [], "is_verified": r.is_verified,
             "source": r.source, "source_url": r.source_url}
            for r in t.reviews if r.is_published
        ],
        technical_level=t.technical_level,
        min_age=t.min_age,
        fitness_level=t.fitness_level,
        highlights=localize(t.highlights, lang),
        included=localize(t.included, lang),
        excluded=localize(t.excluded, lang),
        faqs=_localize_faqs(t.faqs, lang),
        map_embed_url=t.map_embed_url,
        pricing_options=_localize_pricing_options(t.pricing_options, lang),
        route_points=_localize_route_points(t.route_points, lang),
    )


@router.get("", response_model=Page[TourListItem])
def list_tours(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    country: str | None = None,
    destination: str | None = None,
    category: TourCategory | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    search: str | None = None,
    featured: bool | None = Query(None, description="true bo'lsa faqat 'Mashhur turlar' (is_featured) qaytadi"),
    lang: str | None = Depends(get_lang_param),
    db: Session = Depends(get_db),
):
    items, total = tour_crud.list_tours(
        db, page, page_size, country, destination, category, min_price, max_price, search, featured
    )
    return Page(
        items=[_to_list_item(t, lang) for t in items],
        total=total, page=page, page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/{slug}", response_model=TourDetail)
def get_tour(slug: str, lang: str | None = Depends(get_lang_param), db: Session = Depends(get_db)):
    tour = tour_crud.get_by_slug(db, slug)
    if not tour:
        raise HTTPException(status_code=404, detail="Tur topilmadi")
    return _to_detail(tour, lang)


@router.post("", response_model=TourDetail, dependencies=[Depends(require_admin)])
def create_tour(data: TourCreate, db: Session = Depends(get_db)):
    tour = tour_crud.create_tour(db, data)
    return _to_detail(tour, None)


@router.patch("/{tour_id}", response_model=TourDetail, dependencies=[Depends(require_admin)])
def update_tour(tour_id: uuid.UUID, data: TourUpdate, db: Session = Depends(get_db)):
    tour = tour_crud.get_by_id(db, tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tur topilmadi")
    tour = tour_crud.update_tour(db, tour, data)
    return _to_detail(tour, None)


@router.delete("/{tour_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_tour(tour_id: uuid.UUID, db: Session = Depends(get_db)):
    tour = tour_crud.get_by_id(db, tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tur topilmadi")
    tour_crud.delete_tour(db, tour)
