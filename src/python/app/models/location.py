from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    map_id = Column(Integer, ForeignKey("maps.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    min_price = Column(Integer, nullable=True)
    max_price = Column(Integer, nullable=True)
    open_time = Column(Time, nullable=True)
    close_time = Column(Time, nullable=True)
    price_level = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    map = relationship("Map", back_populates="locations")
