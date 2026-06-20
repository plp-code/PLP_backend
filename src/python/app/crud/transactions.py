from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction


async def get_transaction_by_id(db: AsyncSession, transaction_id: int) -> Transaction | None:
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    return result.scalar_one_or_none()


async def get_transaction_by_stripe_id(db: AsyncSession, stripe_payment_intent_id: str) -> Transaction | None:
    result = await db.execute(
        select(Transaction).where(Transaction.stripe_payment_intent_id == stripe_payment_intent_id)
    )
    return result.scalar_one_or_none()


async def get_transactions_by_user(db: AsyncSession, user_id: int) -> list[Transaction]:
    result = await db.execute(select(Transaction).where(Transaction.user_id == user_id))
    return list(result.scalars().all())


async def create_transaction(
    db: AsyncSession,
    user_id: int,
    map_id: int,
    stripe_payment_intent_id: str,
    amount: int,
) -> Transaction:
    transaction = Transaction(
        user_id=user_id,
        map_id=map_id,
        stripe_payment_intent_id=stripe_payment_intent_id,
        amount=amount,
        status="pending",
    )
    db.add(transaction)
    await db.flush()
    return transaction


async def update_transaction_status(db: AsyncSession, transaction: Transaction, status: str) -> Transaction:
    transaction.status = status
    await db.flush()
    return transaction
