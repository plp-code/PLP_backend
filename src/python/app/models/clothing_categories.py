from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from src.python.app.core.database import Base
from src.python.app.models.mixins import TimestampMixin

class ClothingCategory(TimestampMixin, Base):
    __tablename__ = "clothing_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)

    reviews = relationship(
        "Review",
        secondary="review_categories",
        back_populates="categories"
    )
    
    __table_args__ = (
        UniqueConstraint("name", name="uq_clothing_categories_name"),
        UniqueConstraint("slug", name="uq_clothing_categories_slug"),
    )