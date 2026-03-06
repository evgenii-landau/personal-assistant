from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.core.deps import get_current_user
from backend.models.user import User
from backend.schemas.user import UserCreate, UserOut, Token, LinkTelegramRequest
from backend.services.auth_service import register_user, authenticate_user, create_token_for_user, link_telegram

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    user = register_user(db, user_data)
    if not user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": create_token_for_user(user), "token_type": "bearer"}


@router.post("/link-telegram", response_model=UserOut)
def link_telegram_account(
    body: LinkTelegramRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = link_telegram(db, current_user, body.telegram_id)
    if not updated:
        raise HTTPException(status_code=409, detail="Telegram ID already linked to another account")
    return updated
