from sqlalchemy import func
import stripe

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
async def checkout_status(session_id: str, response: Response, db: AsyncSession = Depends(get_db)) -> dict:
    invoice = await crud.invoices.get_by_session_id(db, session_id)
    if not invoice:
        return {"status": "pending"}
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

    if user.hashed_password is not None and not user.is_verified:
        return {"status": "complete", "map_slug": map_.slug, "requires_verification": True}

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

        logger.info(
            f"Creating invoice: user_id={user_id} map_id={map_id} "
            f"session={session_obj['id']} status={status_map[event_type]}"
        )

        try:
            invoice = await crud.invoices.create_invoice(
                db,
                user_id=int(user_id),
                map_id=int(map_id),
                stripe_checkout_session_id=session_obj["id"],
                stripe_payment_intent_id=_field(session_obj, "payment_intent"),
                stripe_customer_id=_field(session_obj, "customer"),
                amount=_field(session_obj, "amount_total", 0),
                currency=_field(session_obj, "currency", "usd"),
                status=status_map[event_type],
            )
        except IntegrityError:
            await db.rollback()
            existing_after_race = await crud.invoices.get_by_session_id(db, session_obj["id"])
            if existing_after_race:
                logger.info(f"Duplicate webhook (confirmed race) ignored: {session_obj['id']}")
                return {"status": "already_processed"}
            logger.exception(f"create_invoice IntegrityError for a NON-duplicate reason: {session_obj['id']}")
            raise

        logger.info(f"Invoice created: id={invoice.id} status={status_map[event_type]}")

        if event_type == "checkout.session.completed":
            await crud.purchases.create_purchase(db, user_id=int(user_id), map_id=int(map_id), invoice_id=invoice.id)
            logger.info(f"Purchase granted: user={user_id} map={map_id}")

            if password_email_args is None:
                user = await crud.users.get_user_by_id(db, int(user_id))
                if user and user.hashed_password is None and user.reset_jti is None:
                    token, jti = create_password_reset_token(user.email)
                    await crud.users.set_reset_jti(db, user.id, jti)
                    password_email_args = (user.email, token, False)

        await db.commit()
        logger.info(f"Webhook committed successfully: session={session_obj['id']} status={status_map[event_type]}")

        if password_email_args:
            try:
                await send_password_reset_email(*password_email_args)
                logger.info(f"Password-set email sent: user={user_id}")
            except Exception:
                logger.exception(f"Failed to send password-set email: user={user_id}")

        return {"status": status_map[event_type]}


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
            await db.commit()
            logger.info(f"Purchase revoked: user={invoice.user_id} map={invoice.map_id}")

        return {"status": "refunded"}

    logger.info(f"Unhandled event type: {event_type}")
    return {"status": "ignored", "reason": "unhandled event"}