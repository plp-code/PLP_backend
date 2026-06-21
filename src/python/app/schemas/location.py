from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field


class LocationMinimalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=255)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    

class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    open_time: time | None = None
    close_time: time | None = None
    price_level: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=1024)


class LocationCreate(LocationBase):
    map_id: int


class LocationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    open_time: time | None = None
    close_time: time | None = None
    price_level: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=1024)


class LocationRead(LocationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    map_id: int
    created_at: datetime
    updated_at: datetime
