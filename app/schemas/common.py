from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar("T")


class Translated(BaseModel):
    uz: str = ""
    ru: str = ""
    en: str = ""


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
