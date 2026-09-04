import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, Field


class ContactMessageCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    message: str = Field(min_length=3, max_length=3000)
    source: str = Field(default="contact", pattern="^(contact|service)$")


class ContactMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    email: EmailStr
    message: str
    source: str
    is_read: bool
    created_at: datetime


class ContactMessageUpdate(BaseModel):
    is_read: bool
