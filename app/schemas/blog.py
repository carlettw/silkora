import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class BlogListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: Any
    slug: str
    cover_image: str | None
    read_time_minutes: int | None
    published_at: datetime | None


class BlogDetail(BlogListItem):
    content: Any


class BlogCreate(BaseModel):
    title: dict
    slug: str
    content: dict
    cover_image: str | None = None
    read_time_minutes: int | None = None
    is_published: bool = True
