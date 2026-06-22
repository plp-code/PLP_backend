from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.python.app.core.database import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)  # PRIMARY already indexes this; no extra index needed
    name = Column(String(255), nullable=False)
    map_id = Column(Integer, ForeignKey("maps.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    min_price = Column(Integer, nullable=True)
    max_price = Column(Integer, nullable=True)
    # PriceLevel enum: 1 = CHEAP, 2 = STANDARD, 3 = EXPENSIVE (see models/enums.py)
    price_level = Column(Integer, nullable=True)
    description = Column(String(1024), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("price_level IN (1, 2, 3)", name="chk_locations_price_level"),
    )

    map = relationship("Map", back_populates="locations")
    hours = relationship(
        "LocationHours",
        back_populates="location",
        cascade="all, delete-orphan",
        order_by="LocationHours.day_of_week",
    )
