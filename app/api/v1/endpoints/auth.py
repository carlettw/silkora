from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.crud import user as user_crud
from app.schemas.user import UserCreate, UserOut, Token, LoginRequest, TokenRefreshRequest
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if user_crud.get_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="Bu email allaqachon ro'yxatdan o'tgan")
    return user_crud.create_user(db, data)


@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = user_crud.get_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email yoki parol noto'g'ri")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Foydalanuvchi bloklangan")

    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=Token)
def refresh(data: TokenRefreshRequest):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token yaroqsiz")

    user_id = payload["sub"]
    return Token(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
