import enum
import uuid

from sqlalchemy import String, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class UserRole(str, enum.Enum):
    customer = "customer"
    agent = "agent"       # B2B / travel agents
    admin = "admin"


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.customer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    preferred_language: Mapped[str] = mapped_column(String(2), default="uz")
