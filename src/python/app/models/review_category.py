from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from src.python.app.core.database import Base
from src.python.app.models.mixins import TimestampMixin

class ReviewCategory(TimestampMixin, Base):
    __tablename__ = "review_categories"

    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, ForeignKey("clothing_categories.id", ondelete="CASCADE"), primary_key=True)