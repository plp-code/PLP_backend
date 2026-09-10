from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, false
from sqlalchemy.orm import relationship

from src.python.app.core.database import Base
from src.python.app.models.mixins import TimestampMixin

class Review(TimestampMixin, Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    experience = Column(String(280), nullable=False)
    item_purchased = Column(String(100), nullable=False)
    is_hidden = Column(Boolean, nullable=False, default=False, server_default=false())
    price_paid = Column(Integer, nullable=True)

    categories = relationship(
        "ClothingCategory",
        secondary="review_categories",
        back_populates="reviews"
    )
    user = relationship("User", back_populates="reviews")
    location = relationship("Location", back_populates="reviews")