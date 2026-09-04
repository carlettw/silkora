import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict


class CountryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: Any  # dict yoki lang= berilsa string
    slug: str
    cover_image: str | None = None
    tour_count: int = 0


class CountryCreate(BaseModel):
    name: dict
    slug: str
    cover_image: str | None = None


class CountryUpdate(BaseModel):
    name: dict | None = None
    slug: str | None = None
    cover_image: str | None = None


class DestinationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: Any
    slug: str
    description: Any | None = None
    cover_image: str | None = None
    country_id: uuid.UUID


class DestinationCreate(BaseModel):
    name: dict
    slug: str
    description: dict | None = None
    cover_image: str | None = None
    country_id: uuid.UUID


class DestinationUpdate(BaseModel):
    name: dict | None = None
    slug: str | None = None
    description: dict | None = None
    cover_image: str | None = None
    country_id: uuid.UUID | None = None
