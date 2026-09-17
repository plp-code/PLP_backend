from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, SmallInteger, Time, false
from sqlalchemy.orm import relationship

from src.python.app.core.database import Base
from src.python.app.models.mixins import TimestampMixin


class LocationHours(TimestampMixin, Base):
    __tablename__ = "location_hours"

    id = Column(Integer, primary_key=True)
    location_id = Column(
        Integer, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    day_of_week = Column(SmallInteger, nullable=False)
    open_time = Column(Time, nullable=True)
    close_time = Column(Time, nullable=True)
    is_closed = Column(Boolean, nullable=False, default=False, server_default=false())
    
    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="chk_location_hours_day_of_week"),
    )

    location = relationship("Location", back_populates="hours")
