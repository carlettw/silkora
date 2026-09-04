import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.user import UserRole


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=8, max_length=72)
    preferred_language: str = "uz"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: EmailStr
    phone: str | None
    role: UserRole
    preferred_language: str
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    preferred_language: str | None = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
