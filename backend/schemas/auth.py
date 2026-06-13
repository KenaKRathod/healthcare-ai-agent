from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field(default="patient", description="Must be one of: patient, doctor, caregiver")


class UserLogin(BaseModel):
    username: str = Field(...)
    password: str = Field(...)


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str


class UserRead(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True
