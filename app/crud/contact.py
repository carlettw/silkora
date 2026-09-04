import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.contact import ContactMessage
from app.schemas.contact import ContactMessageCreate


def create_message(db: Session, data: ContactMessageCreate) -> ContactMessage:
    msg = ContactMessage(**data.model_dump())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def list_messages(db: Session, is_read: bool | None = None) -> list[ContactMessage]:
    query = select(ContactMessage).order_by(ContactMessage.created_at.desc())
    if is_read is not None:
        query = query.where(ContactMessage.is_read == is_read)
    return list(db.execute(query).scalars())


def get_by_id(db: Session, message_id: uuid.UUID) -> ContactMessage | None:
    return db.get(ContactMessage, message_id)


def update_read_status(db: Session, message: ContactMessage, is_read: bool) -> ContactMessage:
    message.is_read = is_read
    db.commit()
    db.refresh(message)
    return message
