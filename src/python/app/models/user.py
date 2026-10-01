from sqlalchemy import Boolean, Column, Integer, String, true, Index, CheckConstraint, false
from sqlalchemy.orm import relationship

from src.python.app.core.database import Base
from src.python.app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    role = Column(String(20), nullable=False, server_default="user")
    is_active = Column(Boolean, nullable=False, default=True, server_default=true())
    magic_link_jti = Column(String(64), nullable=True)
    reset_jti = Column(String(64), nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False, server_default=false())
    
    __table_args__ = (
        Index("ix_users_role", "role"),
        CheckConstraint("role IN ('user', 'admin')", name="ck_users_role"),
    )

    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="user")
    purchases = relationship("Purchase", back_populates="user")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    waitlist_entries = relationship("WaitlistEntries", back_populates="user", cascade="all, delete-orphan")