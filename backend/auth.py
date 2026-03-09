from jose import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from passlib.context import CryptContext

SECRET_KEY = "healthcaresecret"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"])


def hash_password(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    if not isinstance(data, dict) or not data:
        raise ValueError("Token payload must be a non-empty dictionary.")

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(hours=2)

    to_encode.update({"exp": expire})

    try:
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as exc:
        raise ValueError("Failed to create access token.") from exc

    return token


def doctor_only(user: dict):
    role = user.get("role") if isinstance(user, dict) else None
    if role != "doctor":
        raise HTTPException(status_code=403, detail="Doctor access required.")
    return True
