from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.auth import create_access_token, get_current_user
from backend.models import User
from backend.core.security import verify_password, hash_password
from backend.schemas.auth import UserCreate, UserLogin, Token, UserRead

router = APIRouter()


@router.post("/register", response_model=UserRead)
def register(payload: UserCreate, db: Annotated[Session, Depends(get_db)]):
    # Check if user already exists
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Check if role is valid
    if payload.role.lower() not in {"patient", "doctor", "caregiver"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be either 'patient', 'doctor', or 'caregiver'"
        )

    # Create new user
    new_user = User(
        username=payload.username,
        password=hash_password(payload.password),
        role=payload.role.lower()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Annotated[Session, Depends(get_db)]):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Sub is standard JWT subject claim
    token = create_access_token({"sub": user.username})
    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        username=user.username
    )


@router.get("/me", response_model=UserRead)
def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
