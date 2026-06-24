import stripe

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app import crud
from src.python.app.core.database import get_db
from src.python.app.core.config import settings
from src.python.app.core.dependencies import get_current_user
from src.python.app.models import User

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
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create a Stripe Checkout session for purchasing a map."""
    try:
        map_ = await crud.maps.get_map_by_slug(db, map_slug)
        if not map_:
            raise HTTPException(status_code=404, detail="Map not found")

        if await crud.purchases.user_owns_map(db, current_user.id, map_.id):
            raise HTTPException(status_code=400, detail="Map already purchased")
        
        price_in_cents = map_.price
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=current_user.email,
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
                "user_id": str(current_user.id),
                "map_id": str(map_.id)
            },
            success_url=f"{settings.FRONTEND_URL}/maps?success=true&map={map_.name}&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/maps?canceled=true",
        )

        return {"checkout_url": checkout_session.url}
    except HTTPException:
        raise   
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e.user_message))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
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

    logger.info(f"Webhook received: {event_type} | user={user_id} map={map_id}")

    if event_type in {
        "checkout.session.completed",
        "checkout.session.expired",
        "checkout.session.async_payment_failed",
    }:
        if not user_id or not map_id:
            logger.warning(f"Webhook missing metadata: {event_type}")
            return {"status": "ignored", "reason": "missing metadata"}

        
        existing = await crud.invoices.get_by_session_id(db, session_obj["id"])
        if existing:
            logger.info(f"Duplicate webhook ignored: {session_obj['id']}")
            return {"status": "already_processed"}

        status_map = {
            "checkout.session.completed": "paid",
            "checkout.session.expired": "expired",
            "checkout.session.async_payment_failed": "failed",
        }

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

        logger.info(f"Invoice created: id={invoice.id} status={status_map[event_type]}")

        if event_type == "checkout.session.completed":
            await crud.purchases.create_purchase(
                db,
                user_id=int(user_id),
                map_id=int(map_id),
                invoice_id=invoice.id,
            )
            logger.info(f"Purchase granted: user={user_id} map={map_id}")

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
            logger.info(f"Purchase revoked: user={invoice.user_id} map={invoice.map_id}")

        return {"status": "refunded"}

    logger.info(f"Unhandled event type: {event_type}")
    return {"status": "ignored", "reason": "unhandled event"}