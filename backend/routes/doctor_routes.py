from fastapi import APIRouter
from auth import doctor_only

router = APIRouter()

@router.get("/doctor/dashboard")
def doctor_dashboard():

    user = {"role": "doctor"}  # Example user

    doctor_only(user)

    return {"message": "Welcome Doctor"}