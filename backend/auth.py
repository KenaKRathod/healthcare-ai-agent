from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.models import User
from backend.core.security import verify_password, hash_password

SECRET_KEY = "healthcaresecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)


def create_access_token(data: dict):
    if not isinstance(data, dict) or not data:
        raise ValueError("Token payload must be a non-empty dictionary.")

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    try:
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as exc:
        raise ValueError("Failed to create access token.") from exc

    return token


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") or payload.get("user")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


def doctor_only(user: dict | User):
    role = user.role if isinstance(user, User) else user.get("role")
    if role != "doctor":
        raise HTTPException(status_code=403, detail="Doctor access required.")
    return True


def check_role(allowed_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of the roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker
