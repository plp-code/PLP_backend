from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.python.app.schemas.clothing_category import CategoriesRead


class ReviewBase(BaseModel):
    item_purchased: str = Field(..., min_length=1, max_length=100)
    experience: str = Field(..., min_length=1, max_length=280)
    price_paid: int | None = Field(default=None, ge=0)


class ReviewCreate(ReviewBase):
    category_slugs: list[str] = Field(default_factory=list)
    location_id: int | None = None


class ReviewUpdate(BaseModel):
    item_purchased: str | None = Field(default=None, min_length=1, max_length=100)
    experience: str | None = Field(default=None, min_length=1, max_length=280)
    price_paid: int | None = Field(default=None, ge=0)
    category_slugs: list[str] | None = None


class ReviewAuthor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: str | None = None
    last_initial: str | None = Field(default=None, validation_alias="last_name")

    @field_validator("last_initial")
    @classmethod
    def last_initial_only(cls, v: str | None) -> str | None:
        v = (v or "").strip()
        return v[0].upper() if v else None

    @model_validator(mode="after")
    def anonymous_if_unnamed(self) -> "ReviewAuthor":
        # Claimed guest accounts have no names. Never fall back to the email.
        if not (self.first_name or "").strip() and not self.last_initial:
            self.first_name = "Anonymous"
            self.last_initial = None
        return self


class ReviewRead(ReviewBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location_id: int
    user: ReviewAuthor
    categories: list[CategoriesRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ReviewMine(ReviewRead):
    """The caller's own review. Includes is_hidden so the UI can show
    "under moderation"; the public list never returns hidden reviews."""
    is_hidden: bool


class ReviewListResponse(BaseModel):
    reviews: list[ReviewRead]
    total: int = Field(..., ge=0)