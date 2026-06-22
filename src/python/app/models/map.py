from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.python.app.core.database import Base


class Map(Base):
    __tablename__ = "maps"

    id = Column(Integer, primary_key=True)  # PRIMARY already indexes this; no extra index needed
    name = Column(String(255), unique=True, nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    region = Column(String(255), nullable=True)
    price = Column(Integer, nullable=False)
    description = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    locations = relationship("Location", back_populates="map", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="map")
    purchases = relationship("Purchase", back_populates="map")
