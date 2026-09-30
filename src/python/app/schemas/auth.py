from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)
    

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class SetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    
    
class MagicLinkRequest(BaseModel):
    email: EmailStr


class VerifyMagicLinkRequest(BaseModel):
    token: str


class TokenPayload(BaseModel):
    sub: str | None = None
    exp: int | None = None
    type: str | None = None
