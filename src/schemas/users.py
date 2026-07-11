from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional


class UserResponse(BaseModel):
    id: int
    username: str = Field(min_length=2, max_length=100)
    email: EmailStr
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=50)


class ResetPassword(BaseModel):
    new_password: str = Field(min_length=6, max_length=50)
