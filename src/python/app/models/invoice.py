from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String, UniqueConstraint, DateTime, false
from sqlalchemy.orm import relationship

from src.python.app.core.database import Base
from src.python.app.models.mixins import TimestampMixin


class Invoice(TimestampMixin, Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    map_id = Column(Integer, ForeignKey("maps.id", ondelete="CASCADE"), nullable=False)
    stripe_checkout_session_id = Column(String(255), nullable=False)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    amount = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, default="usd", server_default="usd")
    status = Column(String(50), nullable=False, default="pending", server_default="pending")
    session_minted_at = Column(DateTime(timezone=True), nullable=True)
    # True only when the webhook for THIS invoice inserted the user row (guest
    # checkout with a brand-new email). Gates guest auto-login.
    created_user = Column(Boolean, nullable=False, default=False, server_default=false())
    # SHA-256 hex of the checkout_nonce cookie set at create-session, carried
    # through Stripe metadata. Binds auto-login to the buying browser.
    checkout_nonce_hash = Column(String(64), nullable=True)
    failure_reason = Column(String(500), nullable=True)

    purchases = relationship("Purchase", back_populates="invoice")
    user = relationship("User", back_populates="invoices")
    map = relationship("Map", back_populates="invoices")
    
    __table_args__ = (
        UniqueConstraint("stripe_checkout_session_id", name="uq_invoices_stripe_checkout_session_id"),
        UniqueConstraint("stripe_payment_intent_id", name="uq_invoices_stripe_payment_intent_id"),
        Index("ix_invoices_map_id", "map_id"),
    )
