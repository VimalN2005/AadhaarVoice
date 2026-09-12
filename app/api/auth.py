"""
Authentication and JWT Routes.
Handles user registration, login, and operator token verification.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


class UserRegisterSchema(BaseModel):
    username: str
    password: str
    role: Optional[str] = "operator"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency for authenticated endpoints."""
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    username = payload.get("sub")
    if not username:
        return None
    user = db.query(User).filter(User.username == username).first()
    return user


@router.post("/register", response_model=TokenResponse)
def register(user_in: UserRegisterSchema, db: Session = Depends(get_db)):
    """Registers a new administrative or audit operator."""
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        role=user_in.role or "operator",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.username, "role": new_user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": new_user.username,
        "role": new_user.role,
    }


@router.post("/token", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticates credentials and issues a JWT token."""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user.username, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
    }


@router.get("/me")
def get_me(user: Optional[User] = Depends(get_current_user)):
    """Returns profile for currently authenticated user."""
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"id": user.id, "username": user.username, "role": user.role}
