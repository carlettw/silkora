import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_admin
from app.crud import contact as contact_crud
from app.schemas.contact import ContactMessageCreate, ContactMessageOut, ContactMessageUpdate

router = APIRouter(prefix="/contact-messages", tags=["Contact Messages"])


@router.post("", response_model=ContactMessageOut, status_code=201)
def create_contact_message(data: ContactMessageCreate, db: Session = Depends(get_db)):
    """Sayt 'Bog'lanish' yoki 'Xizmat' formasidan kelgan xabar (login talab qilinmaydi)."""
    return contact_crud.create_message(db, data)


@router.get("", response_model=list[ContactMessageOut], dependencies=[Depends(require_admin)])
def list_contact_messages(is_read: bool | None = None, db: Session = Depends(get_db)):
    """Barcha xabarlar ro'yxati (faqat admin)."""
    return contact_crud.list_messages(db, is_read)


@router.patch("/{message_id}", response_model=ContactMessageOut, dependencies=[Depends(require_admin)])
def update_contact_message(message_id: uuid.UUID, data: ContactMessageUpdate, db: Session = Depends(get_db)):
    """Xabarni o'qilgan/o'qilmagan deb belgilash (faqat admin)."""
    message = contact_crud.get_by_id(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Xabar topilmadi")
    return contact_crud.update_read_status(db, message, data.is_read)
