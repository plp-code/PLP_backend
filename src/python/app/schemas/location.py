from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LocationHoursBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0 = Monday ... 6 = Sunday")
    open_time: time | None = None
    close_time: time | None = None
    is_closed: bool = False

    @model_validator(mode="after")
    def check_hours(self):
        if not self.is_closed and (self.open_time is None or self.close_time is None):
            raise ValueError("open_time and close_time are required unless is_closed is true")
        if self.open_time and self.close_time and self.close_time <= self.open_time:
            raise ValueError("close_time must be after open_time")
        return self


class LocationHoursCreate(LocationHoursBase):
    pass


class LocationHoursRead(LocationHoursBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class LocationMinimalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = Field(..., min_length=1, max_length=255)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)



class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    price_level: int | None = None
    description: str | None = Field(default=None, max_length=1024)
    google_place_id: str | None = Field(default=None, max_length=255)
    


class LocationCreate(LocationBase):
    map_id: int
    hours: list[LocationHoursCreate] = []


class LocationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    price_level: int | None = None
    description: str | None = Field(default=None, max_length=1024)
    google_place_id: str | None = Field(default=None, max_length=255)
    hours: list[LocationHoursCreate] | None = None


class LocationRead(LocationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    map_id: int
    hours: list[LocationHoursRead] = []
    created_at: datetime
    updated_at: datetime
