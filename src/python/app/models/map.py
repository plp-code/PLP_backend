from sqlalchemy import Boolean, Column, Integer, String, true, Enum as SQLEnum
from sqlalchemy.orm import relationship

from src.python.app.models.enums import MapStatus
from src.python.app.core.database import Base
from src.python.app.models.mixins import TimestampMixin


class Map(TimestampMixin, Base):
    __tablename__ = "maps"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    region = Column(String(255), nullable=True)
    price = Column(Integer, nullable=False)
    description = Column(String(512), nullable=True)
    status = Column(
        SQLEnum(
            MapStatus, 
            name="map_status",
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=MapStatus.WAITLIST,
        server_default="waitlist"
    )
    
    waitlist = relationship("Waitlist", back_populates="map", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="map", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="map")
    purchases = relationship("Purchase", back_populates="map")
