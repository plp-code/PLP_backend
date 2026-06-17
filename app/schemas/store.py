from pydantic import BaseModel, ConfigDict
from typing import Optional, Any

from app.db.models import PriceLevel

class StoreMinimalResponse(BaseModel):
    id: int
    latitude: float
    longitude: float

    model_config = ConfigDict(from_attributes=True)

class StoreResponse(BaseModel):
    id: int
    store_name: str
    address: str
    price_range: Optional[str] = None
    price_level: Optional[PriceLevel] = None
    price_notes: Optional[str] = None
    notes: Optional[str] = None
    # is_featured: bool
    hours: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)

class StoreCreate(BaseModel):
    store_name: str
    address: str
    latitude: float
    longitude: float
    price_notes: Optional[str] = None
    price_range: Optional[str] = None
    price_level: Optional[PriceLevel] = None
    notes: Optional[str] = None
    hours: Optional[Any] = None 