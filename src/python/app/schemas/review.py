from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

from src.python.app.schemas.clothing_category import CategoriesRead
from src.python.app.schemas.user import UserRead


class ReviewBase(BaseModel):
    item_purchased: str = Field(..., min_length=1, max_length=100)
    experience: str = Field(..., min_length=1, max_length=1024)
    price_paid: float | None = Field(default=None, ge=0)


class ReviewCreate(ReviewBase):
    category_slugs: list[str] = Field(default_factory=list)
    location_id: int | None = None
    is_hidden: bool = False


class ReviewUpdate(BaseModel):
    item_purchased: str | None = Field(default=None, min_length=1, max_length=100)
    experience: str | None = Field(default=None, min_length=1, max_length=1024)
    price_paid: float | None = Field(default=None, ge=0)
    category_slugs: list[str] | None = None


class ReviewRead(ReviewBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location_id: int
    user: UserRead
    categories: list[CategoriesRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ReviewListResponse(BaseModel):
    reviews: list[ReviewRead]
    total: int = Field(..., ge=0)