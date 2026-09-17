from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, false
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.python.app.models.mixins import TimestampMixin
from src.python.app.core.database import Base


class Token(TimestampMixin, Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(512), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_revoked = Column(Boolean, nullable=False, default=False, server_default=false())
    

    user = relationship("User", back_populates="tokens")

    __table_args__ = (
        UniqueConstraint("token", name="uq_tokens_token"),
    )