import enum
from sqlalchemy import JSON, Column, Enum, Float, Integer, String, Boolean, ForeignKey, DateTime, Text, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    """
    Core identity and access table. 
    Manages authentication and billing state.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    has_purchased_map = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    purchased_maps = relationship("UserMapAccess", back_populates="user")
    
    maps = relationship("Map", secondary="user_map_access", viewonly=True)

class Map(Base):
    """
    Stores the metadata and secure embed strings for the curated maps.
    """
    __tablename__ = "maps"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    region = Column(String, nullable=True)
    map_price = Column(Integer, nullable=False)  # Price in cents for precision    
     
    # later to add filtering        
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    shared_with_users = relationship("UserMapAccess", back_populates="map")
    stores = relationship("Store", back_populates="map", cascade="all, delete-orphan")


class UserMapAccess(Base):
    """
    Association Table (Many-to-Many Bridge).
    Explicitly tracks exactly WHICH user bought WHICH map, completely 
    future-proofing your database for a multi-map marketplace.
    """
    __tablename__ = "user_map_access"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    map_id = Column(Integer, ForeignKey("maps.id", ondelete="CASCADE"), nullable=False, index=True)
    
    initial_latitude = Column(Float, nullable=True)
    initial_longitude = Column(Float, nullable=True)

    purchased_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="purchased_maps")
    map = relationship("Map", back_populates="shared_with_users")

    __table_args__ = (
        UniqueConstraint('user_id', 'map_id', name='_user_map_purchase_uc'),
        Index("ix_user_map_access_map_user", "map_id", "user_id"),
    )


class PriceLevel(str, enum.Enum):
    INEXPENSIVE = "inexpensive"
    MODERATE = "moderate"
    EXPENSIVE = "expensive"


class Store(Base):
    """
    Detailed store information linked to a specific map.
    """
    __tablename__ = "stores"
    __table_args__ = (
        Index("ix_stores_map_id_id", "map_id", "id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    map_id = Column(Integer, ForeignKey("maps.id", ondelete="CASCADE"), nullable=False, index=True)

    store_name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    hours = Column(JSON, nullable=True) 
    price_range = Column(String, nullable=True) 
    price_level = Column(Enum(PriceLevel), nullable=True)
    notes = Column(Text, nullable=True)       
    price_notes = Column(Text, nullable=True)
    # is_featured = Column(Boolean, default=False, nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    map = relationship("Map", back_populates="stores")