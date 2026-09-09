from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from src.python.app.core.database import Base
from src.python.app.models.mixins import TimestampMixin
from src.python.app.models.enums import WaitlistEntriesStatus


class WaitlistEntries(TimestampMixin, Base):
    __tablename__ = "waitlist_entries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    map_id = Column(Integer, ForeignKey("maps.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(
        Enum(
            WaitlistEntriesStatus,
            name="waitlist_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=WaitlistEntriesStatus.PENDING,
        server_default=WaitlistEntriesStatus.PENDING.value,
        index=True,
    )
    notified_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="waitlist_entries")
    map = relationship("Map", back_populates="waitlist_entries")

    __table_args__ = (
        UniqueConstraint("user_id", "map_id", name="uq_waitlist_user_map"),
    )