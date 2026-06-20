from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    map_id = Column(Integer, ForeignKey("maps.id", ondelete="CASCADE"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    purchased_at = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "map_id", name="uq_user_map_purchase"),)

    user = relationship("User", back_populates="purchases")
    map = relationship("Map", back_populates="purchases")
    transaction = relationship("Transaction", back_populates="purchase")
