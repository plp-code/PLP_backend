from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.python.app.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True) 
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    map_id = Column(Integer, ForeignKey("maps.id", ondelete="CASCADE"), nullable=False)
    stripe_checkout_session_id = Column(String(255), unique=True, nullable=False) 
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=True) 
    stripe_customer_id = Column(String(255), nullable=True)
    amount = Column(Integer, nullable=False) 
    currency = Column(String(10), nullable=False, default="usd")
    status = Column(String(50), nullable=False, default="pending")
    failure_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    purchases = relationship("Purchase", back_populates="invoice")
    user = relationship("User", back_populates="invoices")
    map = relationship("Map", back_populates="invoices")