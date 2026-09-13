from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClothingCategoryBase(BaseModel):
    id: int | None = None
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=100)

class CategoriesRead(ClothingCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: datetime


class CategoriesCreate(ClothingCategoryBase):
    pass


class CategoriesUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    