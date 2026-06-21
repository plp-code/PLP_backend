from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PurchaseCreate(BaseModel):
    user_id: int
    map_id: int
    invoice_id: int  


class PurchaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    map_id: int
    invoice_id: int
    purchased_at: datetime


class PurchaseWithMap(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    map_name: str
    map_slug: str
    amount: int 
    purchased_at: datetime