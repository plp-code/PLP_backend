import stripe

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app import crud
from src.python.app.core.database import get_db
from src.python.app.core.config import settings
from src.python.app.core.dependencies import get_current_user
from src.python.app.models import User

router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY

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
        
        price_in_cents = int(map_.map_price * 100)
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=current_user.email,
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': map_.title,
                            'description': map_.description or f'Lifetime access to {map_.title}',
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
            success_url=f"{settings.FRONTEND_URL}/maps?success=true&map={map_.title}&session_id={{CHECKOUT_SESSION_ID}}",
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
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    session_obj = event["data"]["object"]
    metadata = session_obj.get("metadata", {})
    user_id = metadata.get("user_id")
    map_id = metadata.get("map_id")

    if event_type in {
        "checkout.session.completed",
        "checkout.session.expired",
        "checkout.session.async_payment_failed",
    }:
        if not user_id or not map_id:
            return {"status": "ignored", "reason": "missing metadata"}

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
            stripe_payment_intent_id=session_obj.get("payment_intent"),
            stripe_customer_id=session_obj.get("customer"),
            amount=session_obj.get("amount_total", 0),
            currency=session_obj.get("currency", "usd"),
            status=status_map[event_type],
        )

        if event_type == "checkout.session.completed":
            await crud.purchases.create_purchase(
                db,
                user_id=int(user_id),
                map_id=int(map_id),
                invoice_id=invoice.id,
            )

        return {"status": status_map[event_type]}

    elif event_type == "charge.refunded":
        payment_intent_id = session_obj.get("payment_intent")
        invoice = await crud.invoices.get_by_payment_intent(db, payment_intent_id)

        if not invoice: 
            return {"status": "ignored", "reason": "invoice not found"}

        invoice.status = "refunded"
        purchase = await crud.purchases.get_by_invoice_id(db, invoice.id)
        
        if purchase:
            await db.delete(purchase)

        return {"status": "refunded"}

    return {"status": "ignored", "reason": "unhandled event"}