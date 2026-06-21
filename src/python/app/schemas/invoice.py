from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InvoiceBase(BaseModel):
    map_id: int
    amount: int = Field(..., ge=0, description="Amount in cents")
    currency: str = Field(default="usd", max_length=10)


class InvoiceCreate(InvoiceBase):
    user_id: int
    stripe_checkout_session_id: str = Field(..., max_length=255)
    stripe_payment_intent_id: str | None = Field(default=None, max_length=255)
    stripe_customer_id: str | None = Field(default=None, max_length=255)


class InvoiceUpdate(BaseModel):
    stripe_payment_intent_id: str | None = Field(default=None, max_length=255)
    stripe_customer_id: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, max_length=50)
    failure_reason: str | None = Field(default=None, max_length=500)


class InvoiceRead(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    stripe_checkout_session_id: str
    stripe_payment_intent_id: str | None = None
    stripe_customer_id: str | None = None
    status: str
    failure_reason: str | None = None
    created_at: datetime
    updated_at: datetime
