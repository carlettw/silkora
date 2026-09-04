import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.i18n import get_lang_param, localize
from app.api.deps import require_admin
from app.crud import geo as geo_crud
from app.schemas.geo import (
    CountryOut, CountryCreate, CountryUpdate,
    DestinationOut, DestinationCreate, DestinationUpdate,
)

router = APIRouter(tags=["Geography"])


@router.get("/countries", response_model=list[CountryOut])
def list_countries(lang: str | None = Depends(get_lang_param), db: Session = Depends(get_db)):
    countries = geo_crud.list_countries(db)
    result = []
    for c, tour_count in countries:
        result.append(CountryOut(id=c.id, name=localize(c.name, lang), slug=c.slug, cover_image=c.cover_image, tour_count=tour_count))
    return result


@router.post("/countries", response_model=CountryOut, dependencies=[Depends(require_admin)])
def create_country(data: CountryCreate, db: Session = Depends(get_db)):
    c = geo_crud.create_country(db, data.name, data.slug, data.cover_image)
    return CountryOut(id=c.id, name=c.name, slug=c.slug, cover_image=c.cover_image)


@router.patch("/countries/{country_id}", response_model=CountryOut, dependencies=[Depends(require_admin)])
def update_country(country_id: uuid.UUID, data: CountryUpdate, db: Session = Depends(get_db)):
    country = geo_crud.get_country_by_id(db, country_id)
    if not country:
        raise HTTPException(status_code=404, detail="Davlat topilmadi")
    country = geo_crud.update_country(db, country, data)
    return CountryOut(id=country.id, name=country.name, slug=country.slug, cover_image=country.cover_image)


@router.delete("/countries/{country_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_country(country_id: uuid.UUID, db: Session = Depends(get_db)):
    country = geo_crud.get_country_by_id(db, country_id)
    if not country:
        raise HTTPException(status_code=404, detail="Davlat topilmadi")

    deps = geo_crud.count_country_dependencies(db, country_id)
    if deps["destinations"] > 0 or deps["tours"] > 0:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Bu davlatni o'chirib bo'lmaydi: unga bog'liq {deps['destinations']} ta yo'nalish "
                f"va {deps['tours']} ta tur mavjud. Avval ularni o'chiring yoki boshqa davlatga o'tkazing."
            ),
        )
    geo_crud.delete_country(db, country)


@router.get("/destinations", response_model=list[DestinationOut])
def list_destinations(
    country_slug: str | None = None,
    lang: str | None = Depends(get_lang_param),
    db: Session = Depends(get_db),
):
    destinations = geo_crud.list_destinations(db, country_slug)
    result = []
    for d in destinations:
        result.append(
            DestinationOut(
                id=d.id,
                name=localize(d.name, lang),
                slug=d.slug,
                description=localize(d.description, lang),
                cover_image=d.cover_image,
                country_id=d.country_id,
            )
        )
    return result


@router.post("/destinations", response_model=DestinationOut, dependencies=[Depends(require_admin)])
def create_destination(data: DestinationCreate, db: Session = Depends(get_db)):
    d = geo_crud.create_destination(db, data)
    return DestinationOut(
        id=d.id, name=d.name, slug=d.slug, description=d.description,
        cover_image=d.cover_image, country_id=d.country_id,
    )


@router.patch("/destinations/{destination_id}", response_model=DestinationOut, dependencies=[Depends(require_admin)])
def update_destination(destination_id: uuid.UUID, data: DestinationUpdate, db: Session = Depends(get_db)):
    destination = geo_crud.get_destination_by_id(db, destination_id)
    if not destination:
        raise HTTPException(status_code=404, detail="Yo'nalish topilmadi")
    destination = geo_crud.update_destination(db, destination, data)
    return DestinationOut(
        id=destination.id, name=destination.name, slug=destination.slug, description=destination.description,
        cover_image=destination.cover_image, country_id=destination.country_id,
    )


@router.delete("/destinations/{destination_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_destination(destination_id: uuid.UUID, db: Session = Depends(get_db)):
    destination = geo_crud.get_destination_by_id(db, destination_id)
    if not destination:
        raise HTTPException(status_code=404, detail="Yo'nalish topilmadi")

    deps = geo_crud.count_destination_dependencies(db, destination_id)
    if deps["tours"] > 0:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Bu yo'nalishni o'chirib bo'lmaydi: unga bog'liq {deps['tours']} ta tur mavjud. "
                f"Avval o'sha turlarni o'chiring yoki boshqa yo'nalishga o'tkazing."
            ),
        )
    geo_crud.delete_destination(db, destination)
