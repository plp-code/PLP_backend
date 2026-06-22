from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, SmallInteger, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.python.app.core.database import Base


class LocationHours(Base):
    __tablename__ = "location_hours"

    id = Column(Integer, primary_key=True)  # PRIMARY already indexes this; no extra index needed
    location_id = Column(
        Integer, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    day_of_week = Column(SmallInteger, nullable=False)  # 0 = Monday ... 6 = Sunday
    open_time = Column(Time, nullable=True)
    close_time = Column(Time, nullable=True)
    is_closed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    location = relationship("Location", back_populates="hours")
