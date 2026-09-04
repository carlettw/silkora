import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.crud import user as user_crud
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Avtorizatsiyadan o'tilmagan",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_error

    user_id = payload.get("sub")
    try:
        user = user_crud.get_by_id(db, uuid.UUID(user_id))
    except (ValueError, TypeError):
        raise credentials_error

    if not user or not user.is_active:
        raise credentials_error

    return user


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if not token:
        return None
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in (UserRole.admin, UserRole.agent):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruxsat yo'q")
    return user
