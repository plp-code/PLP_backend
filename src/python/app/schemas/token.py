from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TokenBase(BaseModel):
    token: str = Field(..., max_length=512)
    expires_at: datetime


class TokenCreate(TokenBase):
    user_id: int


class TokenRead(TokenBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
