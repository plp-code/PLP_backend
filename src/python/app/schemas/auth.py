from pydantic import BaseModel, EmailStr, Field, field_validator

from src.python.app.core.security import MAX_PASSWORD_BYTES, password_too_long


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)
    

class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def password_fits_bcrypt(cls, v: str) -> str:
        if password_too_long(v):
            raise ValueError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes")
        return v

    
class MagicLinkRequest(BaseModel):
    email: EmailStr


class VerfyLinkRequest(BaseModel):
    token: str


class TokenPayload(BaseModel):
    sub: str | None = None
    exp: int | None = None
    type: str | None = None
