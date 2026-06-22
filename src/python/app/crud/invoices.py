from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app.models.invoice import Invoice


async def get_invoice_by_id(db: AsyncSession, invoice_id: int) -> Invoice | None:
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    return result.scalar_one_or_none()


async def get_by_session_id(db: AsyncSession, session_id: str) -> Invoice | None:
    result = await db.execute(
        select(Invoice).where(Invoice.stripe_checkout_session_id == session_id)
    )
    return result.scalar_one_or_none()

async def get_by_payment_intent_id(db: AsyncSession, payment_intent_id: str) -> Invoice | None:
    result = await db.execute(
        select(Invoice).where(Invoice.stripe_payment_intent_id == payment_intent_id)
    )
    return result.scalar_one_or_none()


async def get_invoice_by_checkout_session_id(
    db: AsyncSession, stripe_checkout_session_id: str
) -> Invoice | None:
    result = await db.execute(
        select(Invoice).where(Invoice.stripe_checkout_session_id == stripe_checkout_session_id)
    )
    return result.scalar_one_or_none()


async def get_invoice_by_payment_intent_id(
    db: AsyncSession, stripe_payment_intent_id: str
) -> Invoice | None:
    result = await db.execute(
        select(Invoice).where(Invoice.stripe_payment_intent_id == stripe_payment_intent_id)
    )
    return result.scalar_one_or_none()


async def get_invoices_by_user(db: AsyncSession, user_id: int) -> list[Invoice]:
    result = await db.execute(select(Invoice).where(Invoice.user_id == user_id))
    return list(result.scalars().all())


async def create_invoice(
    db: AsyncSession,
    user_id: int,
    map_id: int,
    stripe_checkout_session_id: str,
    amount: int,
    currency: str = "usd",
    status: str = "pending",
    stripe_payment_intent_id: str | None = None,
    stripe_customer_id: str | None = None,
) -> Invoice:
    invoice = Invoice(
        user_id=user_id,
        map_id=map_id,
        stripe_checkout_session_id=stripe_checkout_session_id,
        stripe_payment_intent_id=stripe_payment_intent_id,
        stripe_customer_id=stripe_customer_id,
        amount=amount,
        currency=currency,
        status=status,
    )
    db.add(invoice)
    await db.flush()
    return invoice


async def update_invoice_status(
    db: AsyncSession,
    invoice: Invoice,
    status: str,
    failure_reason: str | None = None,
) -> Invoice:
    invoice.status = status
    if failure_reason is not None:
        invoice.failure_reason = failure_reason
    await db.flush()
    return invoice
