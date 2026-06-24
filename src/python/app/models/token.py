from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.python.app.core.database import Base


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True)  
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(512), unique=True, nullable=False)  
    expires_at = Column(DateTime, nullable=False, index=True)  
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="tokens")
