import uuid
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.geo import Country, Destination
from app.models.tour import Tour, tour_countries, tour_destinations


def list_countries(db: Session) -> list[tuple[Country, int]]:
    """Har bir davlat uchun faol turlar sonini ham qaytaradi."""
    query = (
        select(Country, func.count(func.distinct(Tour.id)).label("tour_count"))
        .outerjoin(tour_countries, tour_countries.c.country_id == Country.id)
        .outerjoin(Tour, (Tour.id == tour_countries.c.tour_id) & (Tour.is_active == True))  # noqa: E712
        .group_by(Country.id)
    )
    return list(db.execute(query).all())


def get_country_by_slug(db: Session, slug: str) -> Country | None:
    return db.execute(select(Country).where(Country.slug == slug)).scalar_one_or_none()


def create_country(db: Session, name: dict, slug: str, cover_image: str | None) -> Country:
    country = Country(name=name, slug=slug, cover_image=cover_image)
    db.add(country)
    db.commit()
    db.refresh(country)
    return country


def get_country_by_id(db: Session, country_id: uuid.UUID) -> Country | None:
    return db.execute(select(Country).where(Country.id == country_id)).scalar_one_or_none()


def update_country(db: Session, country: Country, data) -> Country:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(country, field, value)
    db.commit()
    db.refresh(country)
    return country


def count_country_dependencies(db: Session, country_id: uuid.UUID) -> dict:
    """Ushbu davlatga bog'liq destinations va tours sonini qaytaradi (o'chirishdan oldin tekshirish uchun)."""
    destinations_count = db.execute(
        select(func.count()).select_from(Destination).where(Destination.country_id == country_id)
    ).scalar_one()
    tours_count = db.execute(
        select(func.count(func.distinct(tour_countries.c.tour_id))).where(tour_countries.c.country_id == country_id)
    ).scalar_one()
    return {"destinations": destinations_count, "tours": tours_count}


def delete_country(db: Session, country: Country) -> None:
    db.delete(country)
    db.commit()


def list_destinations(db: Session, country_slug: str | None = None) -> list[Destination]:
    query = select(Destination)
    if country_slug:
        query = query.join(Destination.country).where(Country.slug == country_slug)
    return list(db.execute(query).scalars())


def get_destination_by_slug(db: Session, slug: str) -> Destination | None:
    return db.execute(select(Destination).where(Destination.slug == slug)).scalar_one_or_none()


def create_destination(db: Session, data) -> Destination:
    destination = Destination(**data.model_dump())
    db.add(destination)
    db.commit()
    db.refresh(destination)
    return destination


def get_destination_by_id(db: Session, destination_id: uuid.UUID) -> Destination | None:
    return db.execute(select(Destination).where(Destination.id == destination_id)).scalar_one_or_none()


def update_destination(db: Session, destination: Destination, data) -> Destination:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(destination, field, value)
    db.commit()
    db.refresh(destination)
    return destination


def count_destination_dependencies(db: Session, destination_id: uuid.UUID) -> dict:
    """Ushbu yo'nalishga bog'liq tours sonini qaytaradi (o'chirishdan oldin tekshirish uchun)."""
    tours_count = db.execute(
        select(func.count(func.distinct(tour_destinations.c.tour_id)))
        .where(tour_destinations.c.destination_id == destination_id)
    ).scalar_one()
    return {"tours": tours_count}


def delete_destination(db: Session, destination: Destination) -> None:
    db.delete(destination)
    db.commit()
