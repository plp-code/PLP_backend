from sqlalchemy import Boolean, Column, Integer, String, true
from sqlalchemy.orm import relationship

from src.python.app.core.database import Base
from src.python.app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default=true())

    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="user")
    purchases = relationship("Purchase", back_populates="user")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    waitlist = relationship("Waitlist", back_populates="user", cascade="all, delete-orphan")
