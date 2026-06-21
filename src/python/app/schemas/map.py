from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.python.app.schemas.location import LocationRead


class MapBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    region: str | None = Field(default=None, max_length=255)
    price: int = Field(..., ge=0)
    description: str | None = Field(default=None, max_length=512)


class MapCreate(MapBase):
    pass


class MapUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    region: str | None = Field(default=None, max_length=255)
    price: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=512)
    is_active: bool | None = None


class MapRead(MapBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_purchased: bool = False
    created_at: datetime
    updated_at: datetime


class MapListRead(MapRead):
    maps: list[MapRead] = []
    total_maps: int = 0
    page: int
    limit: int
    has_more: bool
    

class MapWithLocations(MapRead):
    locations: list[LocationRead] = []
    total_locations: int = 0
    
