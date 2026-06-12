from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
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
    Map Catalog table.
    Stores the metadata and secure embed strings for your curated maps.
    """
    __tablename__ = "maps"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    
    google_embed_url = Column(String, nullable=False) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    shared_with_users = relationship("UserMapAccess", back_populates="map")


class UserMapAccess(Base):
    """
    Association Table (Many-to-Many Bridge).
    Explicitly tracks exactly WHICH user bought WHICH map, completely 
    future-proofing your database for a multi-map marketplace.
    """
    __tablename__ = "user_map_access"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    map_id = Column(Integer, ForeignKey("maps.id", ondelete="CASCADE"), nullable=False)
    
    purchased_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="purchased_maps")
    map = relationship("Map", back_populates="shared_with_users")