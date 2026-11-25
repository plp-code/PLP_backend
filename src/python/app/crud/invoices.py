from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app.models.invoice import Invoice
from src.python.app.models.purchase import Purchase


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


async def user_has_other_paid_invoice(
    db: AsyncSession, user_id: int, exclude_invoice_id: int
) -> bool:
    result = await db.execute(
        select(Invoice.id)
        .where(
            Invoice.user_id == user_id,
            Invoice.status == "paid",
            Invoice.id != exclude_invoice_id,
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def user_has_other_activity(db: AsyncSession, user_id: int, invoice_id: int) -> bool:
    """True if the user has any invoice or purchase other than this invoice's."""
    other_invoice = await db.execute(
        select(Invoice.id)
        .where(Invoice.user_id == user_id, Invoice.id != invoice_id)
        .limit(1)
    )
    if other_invoice.scalar_one_or_none() is not None:
        return True
    other_purchase = await db.execute(
        select(Purchase.id)
        .where(Purchase.user_id == user_id, Purchase.invoice_id != invoice_id)
        .limit(1)
    )
    return other_purchase.scalar_one_or_none() is not None


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
    created_user: bool = False,
    checkout_nonce_hash: str | None = None,
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
        created_user=created_user,
        checkout_nonce_hash=checkout_nonce_hash,
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
