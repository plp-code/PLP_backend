# app/schemas/user.py
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import List

from app.schemas.map import MapResponse 

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True
    first_name: str
    last_name: str

class UserCreate(UserBase):
    password: str 

class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    is_active: bool | None = None

class UserChangePassword(BaseModel):
    current_password: str
    new_password: str

class UserResponse(UserBase):
    id: int
    has_purchased_map: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UserWithMapsResponse(UserResponse):
    maps: List[MapResponse] = []