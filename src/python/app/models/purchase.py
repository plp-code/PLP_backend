from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.python.app.core.database import Base


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    map_id = Column(Integer, ForeignKey("maps.id", ondelete="CASCADE"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    purchased_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "map_id", name="uq_user_map_purchase"),)

    user = relationship("User", back_populates="purchases")
    map = relationship("Map", back_populates="purchases")
    invoice = relationship("Invoice", back_populates="purchases")
