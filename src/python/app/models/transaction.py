from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    map_id = Column(Integer, ForeignKey("maps.id", ondelete="CASCADE"), nullable=False)
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="transactions")
    map = relationship("Map", back_populates="transactions")
    purchase = relationship("Purchase", back_populates="transaction", uselist=False)
