from fastapi import APIRouter
from auth import create_access_token

router = APIRouter()

@router.post("/login")
def login():

    token = create_access_token({"user":"patient"})

    return {
        "access_token": token,
        "role": "patient"
    }