from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.python.app.core.database import Base
from src.python.app.models.mixins import TimestampMixin


class Location(TimestampMixin, Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    map_id = Column(Integer, ForeignKey("maps.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    min_price = Column(Integer, nullable=True)
    max_price = Column(Integer, nullable=True)
    google_place_id = Column(String(255), unique=True, nullable=True)
    price_level = Column(Integer, nullable=True)
    description = Column(String(1024), nullable=True)
    neighborhood = Column(String(255), nullable=False, default="Unknown", server_default="Unknown")

    __table_args__ = (
        CheckConstraint("price_level IS NULL OR price_level BETWEEN 1 AND 4", name="chk_locations_price_level"),
        CheckConstraint("min_price IS NULL OR max_price IS NULL OR min_price <= max_price", name="chk_locations_price_range"),
    )
    
    

    map = relationship("Map", back_populates="locations")
    reviews = relationship("Review", back_populates="location", cascade="all, delete-orphan")
    hours = relationship(
        "LocationHours",
        back_populates="location",
        cascade="all, delete-orphan",
        order_by="LocationHours.day_of_week",
    )
