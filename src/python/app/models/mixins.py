from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func


class TimestampMixin:
    """Adds ``created_at`` / ``updated_at`` columns populated by the database.

    Both default to the server clock on insert; ``updated_at`` is bumped on
    every update. Marked ``NOT NULL`` since the server default always fills them.
    """

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
