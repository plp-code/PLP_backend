# app/schemas/map.py
from pydantic import BaseModel, ConfigDict
from typing import Optional

class MapBase(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None

class MapResponse(MapBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class MapResponseSecure(MapResponse):
    google_embed_url: str