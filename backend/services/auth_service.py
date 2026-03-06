from sqlalchemy.orm import Session

from backend.models.user import User
from backend.schemas.user import UserCreate
from backend.core.security import hash_password, verify_password, create_access_token


def register_user(db: Session, user_data: UserCreate) -> User | None:
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        return None
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_token_for_user(user: User) -> str:
    return create_access_token({"sub": str(user.id)})


def link_telegram(db: Session, user: User, telegram_id: int) -> User | None:
    """Attach a Telegram user ID to an existing account.

    Returns the updated user, or None if the telegram_id is already taken
    by a different account.
    """
    conflict = (
        db.query(User)
        .filter(User.telegram_id == telegram_id, User.id != user.id)
        .first()
    )
    if conflict:
        return None
    user.telegram_id = telegram_id
    db.commit()
    db.refresh(user)
    return user
