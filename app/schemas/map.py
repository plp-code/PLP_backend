from pydantic import BaseModel, ConfigDict
from typing import Optional

class MapBase(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    region: Optional[str] = None
    map_price: int 

class MapCreate(MapBase):
    pass

class MapResponse(MapBase):
    id: int
    has_access: bool = False 
    
    model_config = ConfigDict(from_attributes=True)
