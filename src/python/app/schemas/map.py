from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from src.python.app.models.enums import MapStatus
from src.python.app.schemas.location import LocationRead


class MapBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    region: str | None = Field(default=None, max_length=255)
    price: int = Field(..., ge=0)
    description: str | None = Field(default=None, max_length=512)


class MapCreate(MapBase):
    status: MapStatus = MapStatus.WAITLIST


class MapUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    region: str | None = Field(default=None, max_length=255)
    price: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=512)
    status: MapStatus | None = None  


class MapSummary(MapBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: MapStatus             
    is_purchased: bool = False
    is_waitlisted: bool = False   


class MapListResponse(BaseModel):
    maps: list[MapSummary]
    total: int
    page: int
    limit: int
    has_more: bool


class MapRead(MapBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: MapStatus             
    created_at: datetime
    updated_at: datetime


class MapDetail(MapBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: MapStatus             
    is_purchased: bool = True
    locations: list[LocationRead] = []
    total_locations: int = 0