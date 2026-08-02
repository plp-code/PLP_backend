from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.python.app.core.database import Base
from src.python.app.models.mixins import TimestampMixin


class Invoice(TimestampMixin, Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    map_id = Column(Integer, ForeignKey("maps.id", ondelete="CASCADE"), nullable=False)
    stripe_checkout_session_id = Column(String(255), unique=True, nullable=False)
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    amount = Column(Integer, nullable=False)
    currency = Column(String(10), nullable=False, default="usd", server_default="usd")
    status = Column(String(50), nullable=False, default="pending", server_default="pending")
    failure_reason = Column(String(500), nullable=True)

    purchases = relationship("Purchase", back_populates="invoice")
    user = relationship("User", back_populates="invoices")
    map = relationship("Map", back_populates="invoices")
