from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class ContactMessage(UUIDPKMixin, TimestampMixin, Base):
    """Sayt 'Bog'lanish' yoki 'Xizmat' formalaridan kelgan xabarlar."""
    __tablename__ = "contact_messages"

    name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(30), default="contact")  # "contact" | "service"
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
