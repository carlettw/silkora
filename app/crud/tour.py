import uuid

from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.models.tour import Tour, TourItineraryDay, TourImage, TourCategory
from app.models.geo import Country, Destination
from app.schemas.tour import TourCreate, TourUpdate, TourItineraryDayCreate, TourPricingOptionCreate


def _pricing_options_to_dicts(options: list[TourPricingOptionCreate]) -> list[dict]:
    """Har bir narx variantiga (agar berilmagan bo'lsa) yangi UUID id beradi."""
    result = []
    for opt in options:
        d = opt.model_dump()
        d["id"] = d["id"] or str(uuid.uuid4())
        d["price"] = float(d["price"])
        result.append(d)
    return result


def _create_itinerary_day(db: Session, tour_id: uuid.UUID, day: TourItineraryDayCreate) -> None:
    db.add(TourItineraryDay(
        tour_id=tour_id,
        day_number=day.day_number,
        title=day.title,
        description=day.description,
        what_to_expect=day.what_to_expect,
        meals_included=day.meals_included,
        transportation=day.transportation,
        gallery=day.gallery,
        accommodation=day.accommodation,
    ))


def _base_query():
    return select(Tour).options(
        selectinload(Tour.countries),
        selectinload(Tour.destinations),
        selectinload(Tour.images),
        selectinload(Tour.itinerary),
        selectinload(Tour.reviews),
    )


def _list_query():
    """Ro'yxat (kartochka) ko'rinishi uchun yengil so'rov - faqat TourListItem uchun kerak bo'lgan
    bog'lanishlarni yuklaydi (countries). Bu har bir ortiqcha selectinload bilan qo'shiladigan
    tarmoq aylanishini (round-trip) kamaytiradi - ayniqsa backend va baza turli mintaqada bo'lganda muhim."""
    return select(Tour).options(
        selectinload(Tour.countries),
    )


def get_by_slug(db: Session, slug: str) -> Tour | None:
    return db.execute(_base_query().where(Tour.slug == slug)).scalar_one_or_none()


def get_by_id(db: Session, tour_id: uuid.UUID) -> Tour | None:
    return db.execute(_base_query().where(Tour.id == tour_id)).scalar_one_or_none()


def list_tours(
    db: Session,
    page: int = 1,
    page_size: int = 12,
    country_slug: str | None = None,
    destination_slug: str | None = None,
    category: TourCategory | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    search: str | None = None,
    featured: bool | None = None,
) -> tuple[list[Tour], int]:
    query = _list_query().where(Tour.is_active == True)  # noqa: E712

    if country_slug:
        query = query.join(Tour.countries).where(Country.slug == country_slug)
    if destination_slug:
        query = query.join(Tour.destinations).where(Destination.slug == destination_slug)
    if category:
        query = query.where(Tour.category == category)
    if min_price is not None:
        query = query.where(Tour.price >= min_price)
    if max_price is not None:
        query = query.where(Tour.price <= max_price)
    if featured is not None:
        query = query.where(Tour.is_featured == featured)
    if search:
        # JSONB matnida sodda qidiruv (uz/ru/en barcha kalitlar bo'ylab)
        query = query.where(func.cast(Tour.title, __import__("sqlalchemy").String).ilike(f"%{search}%"))

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    items = list(db.execute(query).scalars().unique())
    return items, total


def create_tour(db: Session, data: TourCreate) -> Tour:
    tour = Tour(
        title=data.title,
        slug=data.slug,
        short_description=data.short_description,
        description=data.description,
        category=data.category,
        duration_days=data.duration_days,
        duration_nights=data.duration_nights,
        price=data.price,
        currency=data.currency,
        cover_image=data.cover_image,
        max_group_size=data.max_group_size,
        is_featured=data.is_featured,
        technical_level=data.technical_level,
        min_age=data.min_age,
        fitness_level=data.fitness_level,
        highlights=data.highlights,
        included=data.included,
        excluded=data.excluded,
        faqs=data.faqs,
        map_embed_url=data.map_embed_url,
        pricing_options=_pricing_options_to_dicts(data.pricing_options),
        route_points=[rp.model_dump() for rp in data.route_points],
    )
    if data.country_ids:
        tour.countries = db.query(Country).filter(Country.id.in_(data.country_ids)).all()
    if data.destination_ids:
        tour.destinations = db.query(Destination).filter(Destination.id.in_(data.destination_ids)).all()

    db.add(tour)
    db.flush()  # tour.id kerak bo'ladi itinerary/rasmlar uchun

    for day in data.itinerary:
        _create_itinerary_day(db, tour.id, day)

    for idx, url in enumerate(data.images):
        db.add(TourImage(tour_id=tour.id, image_url=url, order=idx))

    db.commit()
    db.refresh(tour)
    return get_by_id(db, tour.id)


def update_tour(db: Session, tour: Tour, data: TourUpdate) -> Tour:
    update_data = data.model_dump(
        exclude_unset=True, exclude={"country_ids", "destination_ids", "images", "itinerary", "pricing_options"}
    )
    for field, value in update_data.items():
        setattr(tour, field, value)

    if data.country_ids is not None:
        tour.countries = db.query(Country).filter(Country.id.in_(data.country_ids)).all()
    if data.destination_ids is not None:
        tour.destinations = db.query(Destination).filter(Destination.id.in_(data.destination_ids)).all()

    if data.pricing_options is not None:
        tour.pricing_options = _pricing_options_to_dicts(data.pricing_options)

    if data.images is not None:
        # Galereya rasmlarini to'liq almashtiramiz (eskilarini o'chirib, yangilarini kiritamiz)
        db.query(TourImage).filter(TourImage.tour_id == tour.id).delete()
        for idx, url in enumerate(data.images):
            db.add(TourImage(tour_id=tour.id, image_url=url, order=idx))

    if data.itinerary is not None:
        # Kunlik dasturni to'liq almashtiramiz (eskilarini o'chirib, yangilarini kiritamiz)
        db.query(TourItineraryDay).filter(TourItineraryDay.tour_id == tour.id).delete()
        for day in data.itinerary:
            _create_itinerary_day(db, tour.id, day)

    db.commit()
    db.refresh(tour)
    return get_by_id(db, tour.id)


def delete_tour(db: Session, tour: Tour) -> None:
    db.delete(tour)
    db.commit()
