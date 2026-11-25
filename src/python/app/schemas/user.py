from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.python.app.core.security import MAX_PASSWORD_BYTES, password_too_long


class UserBase(BaseModel):
    email: EmailStr
    first_name: str | None = Field(..., min_length=1, max_length=255)
    last_name: str | None = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, v: str) -> str:
        if password_too_long(v):
            raise ValueError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes")
        return v


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = Field(default=None, min_length=1, max_length=255)
    last_name: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None
    

class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserMe(UserRead):
    """/users/me only. has_password drives the frontend's guest banner; the
    hash itself is never part of any schema."""
    has_password: bool

    @classmethod
    def from_user(cls, user) -> "UserMe":
        base = UserRead.model_validate(user).model_dump()
        return cls(**base, has_password=user.hashed_password is not None)

    
