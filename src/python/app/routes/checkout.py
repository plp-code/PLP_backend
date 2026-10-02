from sqlalchemy import func
import stripe
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Header, Request, Response
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app import crud
from src.python.app.core.database import get_db
from src.python.app.core.config import settings
from src.python.app.core.jwt import create_password_reset_token
from src.python.app.core.email import send_password_reset_email
from src.python.app.core.dependencies import get_current_user_optional
from src.python.app.models import User
from src.python.app.models import Invoice

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY


def _field(obj, key, default=None):
    """Safe accessor for Stripe objects/dicts.

    stripe>=8 StripeObject is not a dict subclass and has no .get(), but it does
    support `in` and `[]`. This works for both StripeObject and plain dicts.
    """
    return obj[key] if obj is not None and key in obj else default


async def _refund_duplicate_purchase(
    payment_intent_id: str | None, session_id: str, user_id: int, map_id: int
) -> None:
    """Refund a charge for a map the user already owns. Never raises."""
    if not payment_intent_id:
        logger.error(f"DUPLICATE PURCHASE but no payment_intent, refund manually: session={session_id}")
        return
    try:
        await asyncio.to_thread(
            stripe.Refund.create,
            payment_intent=payment_intent_id,
            reason="duplicate",
            metadata={
                "checkout_session_id": session_id,
                "user_id": str(user_id),
                "map_id": str(map_id),
            },
            idempotency_key=f"duplicate-refund-{session_id}",
        )
        logger.info(f"Duplicate purchase refunded: session={session_id} pi={payment_intent_id}")
    except Exception:
        logger.exception(f"Auto-refund FAILED, refund manually: session={session_id} pi={payment_intent_id}")


@router.post("/create-session")
async def create_checkout_session(
    map_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional)
) -> dict:
    """Create a Stripe Checkout session for purchasing a map."""
    logger.info(f"create-session called: map_slug={map_slug} user={'guest' if not current_user else current_user.id}")
    try:
        map_ = await crud.maps.get_map_by_slug(db, map_slug)
        if not map_:
            logger.warning(f"create-session: map not found for slug={map_slug}")
            raise HTTPException(status_code=404, detail="Map not found")

        if current_user and await crud.purchases.user_owns_map(db, current_user.id, map_.id):
            logger.info(f"create-session: user={current_user.id} already owns map={map_.id}")
            raise HTTPException(status_code=400, detail="Map already purchased")

        price_in_cents = map_.price
        logger.info(f"create-session: creating Stripe session for map_id={map_.id} price_cents={price_in_cents}")

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=current_user.email if current_user else None,
            customer_creation="always",
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': map_.name,
                            'description': map_.description or f'Lifetime access to {map_.name}',
                        },
                        'unit_amount': price_in_cents,
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            metadata={
                "user_id": str(current_user.id) if current_user else "",
                "map_id": str(map_.id)
            },
            success_url=f"{settings.FRONTEND_URL}/checkout/complete?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/maps?canceled=true",
        )

        logger.info(f"create-session: Stripe session created id={checkout_session.id} map_id={map_.id}")
        return {"checkout_url": checkout_session.url}

    except HTTPException:
        raise
    except stripe.error.StripeError as e:
        logger.error(f"create-session: Stripe error - {e.user_message}")
        raise HTTPException(status_code=400, detail=str(e.user_message))
    except Exception:
        logger.exception("create-session: unexpected error")
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again.")


@router.get("/status/{session_id}")
async def checkout_status(
    session_id: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> dict:
    invoice = await crud.invoices.get_by_session_id(db, session_id)
    if not invoice:
        return {"status": "pending"}

    if invoice.status in ("duplicate", "refunded"):
        if await crud.purchases.user_owns_map(db, invoice.user_id, invoice.map_id):
            map_ = await crud.maps.get_map_by_id(db, invoice.map_id)
            return {
                "status": "already_owned",
                "map_slug": map_.slug if map_ else None,
                "logged_in": current_user is not None and current_user.id == invoice.user_id,
            }
        return {"status": invoice.status}

    if invoice.status != "paid":
        return {"status": invoice.status}

    purchase = await crud.purchases.get_by_invoice_id(db, invoice.id)
    if not purchase:
        return {"status": "pending"}

    map_ = await crud.maps.get_map_by_id(db, invoice.map_id)
    if not map_:
        logger.warning(f"checkout-status: map not found for id={invoice.map_id}")
        raise HTTPException(status_code=404, detail="Map not found")

    user = await crud.users.get_user_by_id(db, invoice.user_id)
    if not user:
        logger.warning(f"checkout-status: user not found for id={invoice.user_id}")
        raise HTTPException(status_code=404, detail="User not found")

    if current_user is not None and current_user.id == user.id:
        return {"status": "complete", "map_slug": map_.slug}

    if user.hashed_password is not None:
        return {"status": "complete", "map_slug": map_.slug, "requires_login": True}

    result = await db.execute(
        update(Invoice)
        .where(Invoice.id == invoice.id, Invoice.session_minted_at.is_(None))
        .values(session_minted_at=func.now())
    )
    if result.rowcount == 1:
        await crud.auth.set_session_cookies(response, db, invoice.user_id)
        await db.commit()

    return {"status": "complete", "map_slug": map_.slug}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str | None = Header(None, alias="stripe-signature"),
) -> dict:
    """Handle Stripe webhook events."""
    if not stripe_signature:
        logger.warning("Webhook called with no stripe-signature header")
        raise HTTPException(status_code=400, detail="Missing 'stripe-signature' header.")

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        logger.warning("Webhook received with invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.warning("Webhook received with invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    session_obj = event["data"]["object"]
    metadata = _field(session_obj, "metadata", {})
    user_id = _field(metadata, "user_id")
    map_id = _field(metadata, "map_id")

    logger.info(
        f"Webhook received: type={event_type} event_id={event['id']} "
        f"session_id={_field(session_obj, 'id')} user_id={user_id!r} map_id={map_id!r}"
    )

    if event_type in {
        "checkout.session.completed",
        "checkout.session.expired",
        "checkout.session.async_payment_failed",
    }:
        if not map_id:
            logger.warning(f"Webhook missing map_id: {event_type} session={session_obj['id']}")
            return {"status": "ignored", "reason": "missing map_id"}

        existing = await crud.invoices.get_by_session_id(db, session_obj["id"])
        if existing:
            logger.info(f"Duplicate webhook ignored (invoice already exists): {session_obj['id']}")
            return {"status": "already_processed"}

        password_email_args = None

        if not user_id:
            if event_type != "checkout.session.completed":
                logger.info(f"Ignoring {event_type} for guest session with no prior user: {session_obj['id']}")
                return {"status": "ignored", "reason": "guest session incomplete"}

            customer_details = _field(session_obj, "customer_details", {})
            email = _field(customer_details, "email")
            logger.info(f"Guest checkout detected, customer_details={customer_details!r} resolved_email={email!r}")

            if not email:
                logger.warning(f"Guest checkout with no email: {session_obj['id']}")
                return {"status": "ignored", "reason": "no email on guest session"}

            guest_user, password_email_args = await crud.users.get_or_create_pending(db, email)
            user_id = guest_user.id
            logger.info(f"Resolved guest email={email} to user_id={user_id}")

        status_map = {
            "checkout.session.completed": "paid",
            "checkout.session.expired": "expired",
            "checkout.session.async_payment_failed": "failed",
        }

        session_id = session_obj["id"]
        payment_intent_id = _field(session_obj, "payment_intent")
        user_id_int = int(user_id)
        map_id_int = int(map_id)
        final_status = status_map[event_type]

        logger.info(
            f"Creating invoice: user_id={user_id_int} map_id={map_id_int} "
            f"session={session_id} status={final_status}"
        )

        try:
            invoice = await crud.invoices.create_invoice(
                db,
                user_id=user_id_int,
                map_id=map_id_int,
                stripe_checkout_session_id=session_id,
                stripe_payment_intent_id=payment_intent_id,
                stripe_customer_id=_field(session_obj, "customer"),
                amount=_field(session_obj, "amount_total", 0),
                currency=_field(session_obj, "currency", "usd"),
                status=final_status,
            )
        except IntegrityError:
            await db.rollback()
            existing_after_race = await crud.invoices.get_by_session_id(db, session_id)
            if existing_after_race:
                logger.info(f"Duplicate webhook (confirmed race) ignored: {session_id}")
                return {"status": "already_processed"}
            logger.exception(f"create_invoice IntegrityError for a NON-duplicate reason: {session_id}")
            raise

        logger.info(f"Invoice created: id={invoice.id} status={final_status}")

        duplicate_purchase = False

        if event_type == "checkout.session.completed":
            try:
                async with db.begin_nested():
                    await crud.purchases.create_purchase(
                        db, user_id=user_id_int, map_id=map_id_int, invoice_id=invoice.id
                    )
            except IntegrityError:                
                if not await crud.purchases.user_owns_map(db, user_id_int, map_id_int):
                    logger.exception(f"create_purchase IntegrityError for a NON-duplicate reason: {session_id}")
                    raise
                duplicate_purchase = True
                invoice.status = "duplicate" 
                logger.warning(
                    f"DUPLICATE PURCHASE: user={user_id_int} map={map_id_int} "
                    f"invoice={invoice.id} session={session_id}"
                )
            else:
                logger.info(f"Purchase granted: user={user_id_int} map={map_id_int}")

            await crud.waitlist.mark_joined(db, user_id=user_id_int, map_id=map_id_int)

            if password_email_args is None:
                user = await crud.users.get_user_by_id(db, user_id_int)
                if user and user.hashed_password is None and user.reset_jti is None:
                    token, jti = create_password_reset_token(user.email)
                    await crud.users.set_reset_jti(db, user.id, jti)
                    password_email_args = (user.email, token, False)

        await db.commit()
        logger.info(f"Webhook committed successfully: session={session_id} status={final_status}")
        
        if duplicate_purchase:
            await _refund_duplicate_purchase(payment_intent_id, session_id, user_id_int, map_id_int)

        if password_email_args:
            try:
                await send_password_reset_email(*password_email_args)
                logger.info(f"Password-set email sent: user={user_id_int}")
            except Exception:
                logger.exception(f"Failed to send password-set email: user={user_id_int}")

        return {"status": "duplicate_refunded" if duplicate_purchase else final_status}

    elif event_type == "refund.created":
        refund_obj = event["data"]["object"]
        payment_intent_id = _field(refund_obj, "payment_intent")

        invoice = await crud.invoices.get_by_payment_intent_id(db, payment_intent_id)

        if not invoice:
            logger.warning(f"Refund webhook: invoice not found for {payment_intent_id}")
            return {"status": "ignored", "reason": "invoice not found"}

        invoice.status = "refunded"
        purchase = await crud.purchases.get_by_invoice_id(db, invoice.id)

        if purchase:
            await db.delete(purchase)
            logger.info(f"Purchase revoked: user={invoice.user_id} map={invoice.map_id}")

        await db.commit()
        return {"status": "refunded"}

    logger.info(f"Unhandled event type: {event_type}")
    return {"status": "ignored", "reason": "unhandled event"}