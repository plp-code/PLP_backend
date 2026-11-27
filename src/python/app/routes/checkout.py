from sqlalchemy import func
import hashlib
import hmac
import secrets
import stripe
import asyncio
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, HTTPException, Header, Request, Response
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app import crud
from src.python.app.core.database import get_db
from src.python.app.core.config import settings
from src.python.app.core.email import send_checkout_magic_link_email, normalize_email
from src.python.app.core.jwt import set_auth_cookie
from src.python.app.core.rate_limit import hit_key_limit
from src.python.app.core.dependencies import get_current_user_optional
from src.python.app.models import User
from src.python.app.models import Invoice
from src.python.app.models.enums import MapStatus

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
    payment_intent_id: str | None, session_id: str, user_id: int, map_id: int,
    reason: str = "duplicate",
) -> None:
    """Refund a charge we can't fulfil (duplicate map / inactive account). Never raises."""
    if not payment_intent_id:
        logger.error(f"DUPLICATE PURCHASE but no payment_intent, refund manually: session={session_id}")
        return
    try:
        await asyncio.to_thread(
            stripe.Refund.create,
            payment_intent=payment_intent_id,
            reason=reason,
            metadata={
                "checkout_session_id": session_id,
                "user_id": str(user_id),
                "map_id": str(map_id),
            },
            idempotency_key=f"{reason}-refund-{session_id}",
        )
        logger.info(f"Duplicate purchase refunded: session={session_id} pi={payment_intent_id}")
    except Exception:
        logger.exception(f"Auto-refund FAILED, refund manually: session={session_id} pi={payment_intent_id}")


async def _resolve_email(session_obj) -> str | None:
    details = _field(session_obj, "customer_details", {}) or {}
    email = _field(details, "email") or _field(session_obj, "customer_email")

    if not email and (cid := _field(session_obj, "customer")):
        try:
            customer = await run_in_threadpool(stripe.Customer.retrieve, cid)
            email = customer.email
        except stripe.error.StripeError:
            logger.exception(f"Customer lookup failed: {cid}")

    return normalize_email(email)


CHECKOUT_NONCE_COOKIE = "checkout_nonce"
CHECKOUT_NONCE_MAX_AGE = 24 * 60 * 60  # Stripe Checkout sessions expire within 24h
CHECKOUT_LINK_VALID_FOR = "60 minutes"  # must match crud.auth.CHECKOUT_MAGIC_LINK_TTL


def _hash_nonce(nonce: str) -> str:
    return hashlib.sha256(nonce.encode()).hexdigest()


def _nonce_matches(nonce: str | None, expected_hash: str | None) -> bool:
    if not nonce or not expected_hash:
        return False
    return hmac.compare_digest(_hash_nonce(nonce), expected_hash)


def _mask_email(email: str | None) -> str | None:
    """j***@gmail.com. Never returns more than the first character of the local part."""
    if not email or "@" not in email:
        return None
    local, _, domain = email.partition("@")
    return f"{local[:1]}***@{domain}"


async def _build_checkout_link_args(db: AsyncSession, user: User, map_id: int) -> tuple | None:
    """Issue a 60-minute one-time sign-in link to the bought map, for a
    passwordless active user. Replaces any earlier magic link. Returns args for
    _send_checkout_link_safe, or None (user has a password: they log in
    normally, and nothing is sent). Does not commit."""
    if user.hashed_password is not None or not user.is_active:
        return None
    map_ = await crud.maps.get_map_by_id(db, map_id)
    if map_ is None:
        return None
    return_to = crud.auth.safe_return_path(f"/maps/{map_.slug}")
    token = await crud.auth.create_magic_link_token(
        db, user.id, ttl=crud.auth.CHECKOUT_MAGIC_LINK_TTL, return_to=return_to,
    )
    return normalize_email(user.email), token, map_.name, return_to


async def _send_checkout_link_safe(email: str, token: str, map_name: str, return_to: str) -> None:
    try:
        await send_checkout_magic_link_email(
            email, token, map_name=map_name, return_to=return_to, valid_for=CHECKOUT_LINK_VALID_FOR,
        )
        logger.info(f"Checkout sign-in email sent: return_to={return_to}")
    except Exception:
        logger.exception("Failed to send checkout sign-in email")


@router.post("/create-session")
async def create_checkout_session(
    map_slug: str,
    response: Response,
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

        if map_.status != MapStatus.LIVE:
            logger.warning(f"create-session: map_id={map_.id} not purchasable, status={map_.status}")
            raise HTTPException(status_code=400, detail="This map is not available for purchase")

        if current_user and await crud.purchases.user_owns_map(db, current_user.id, map_.id):
            logger.info(f"create-session: user={current_user.id} already owns map={map_.id}")
            raise HTTPException(status_code=400, detail="Map already purchased")

        price_in_cents = map_.price
        logger.info(f"create-session: creating Stripe session for map_id={map_.id} price_cents={price_in_cents}")

        # Binds any later guest auto-login to this browser. Only the hash leaves
        # the server (via Stripe metadata); the raw nonce lives in an HttpOnly cookie.
        checkout_nonce = secrets.token_urlsafe(32)

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
                "map_id": str(map_.id),
                "checkout_nonce_hash": _hash_nonce(checkout_nonce),
            },
            success_url=f"{settings.FRONTEND_URL}/checkout/complete?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/maps?canceled=true",
        )

        logger.info(f"create-session: Stripe session created id={checkout_session.id} map_id={map_.id}")
        set_auth_cookie(
            response, CHECKOUT_NONCE_COOKIE, checkout_nonce,
            max_age=CHECKOUT_NONCE_MAX_AGE, path="/api/v1/checkout",
        )
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
    checkout_nonce: str | None = Cookie(default=None, alias=CHECKOUT_NONCE_COOKIE),
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

    # Logged-in purchase: the caller already holds a valid session for this user.
    if current_user is not None and current_user.id == user.id:
        return {"status": "complete", "map_slug": map_.slug}

    # Guest auto-login. The email on a guest invoice was typed at Stripe and is
    # unverified, so a session is only minted when this invoice created a
    # brand-new, otherwise-empty account AND the poll comes from the browser
    # that started checkout. Anything else must log in via email.
    can_mint = (
        invoice.created_user
        and user.hashed_password is None
        and user.is_active
        and _nonce_matches(checkout_nonce, invoice.checkout_nonce_hash)
        and not await crud.invoices.user_has_other_activity(db, user.id, invoice.id)
    )
    if can_mint:
        result = await db.execute(
            update(Invoice)
            .where(Invoice.id == invoice.id, Invoice.session_minted_at.is_(None))
            .values(session_minted_at=func.now())
        )
        if result.rowcount == 1:
            await db.commit()
            crud.auth.set_guest_session_cookie(response, user.id)
            return {"status": "complete", "map_slug": map_.slug}

    # The webhook already sent a claim link to passwordless users;
    # POST /checkout/resend-claim sends a fresh one.
    return {
        "status": "complete",
        "map_slug": map_.slug,
        "requires_login": True,
        "email_hint": _mask_email(user.email),
    }


class ResendClaimRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=255)


RESEND_CLAIM_PER_SESSION_LIMIT = 3
RESEND_CLAIM_PER_SESSION_WINDOW = 15 * 60
_RESEND_CLAIM_ACCEPTED = {"status": "accepted"}


@router.post("/resend-claim", status_code=202)
async def resend_claim(
    body: ResendClaimRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Send a fresh one-time sign-in link to the map bought in this session.

    Only passwordless users get one; it replaces any earlier link. Always 202
    with the same body, whether or not anything was sent, so the response
    reveals nothing about the session or the account. Per-IP limit is in the
    rate-limit middleware; per-session limit is here (silently skips).
    """
    if await hit_key_limit(
        f"resend-claim:{body.session_id}",
        RESEND_CLAIM_PER_SESSION_LIMIT,
        RESEND_CLAIM_PER_SESSION_WINDOW,
    ):
        invoice = await crud.invoices.get_by_session_id(db, body.session_id)
        user = await crud.users.get_user_by_id(db, invoice.user_id) if invoice else None
        if user is not None:
            args = await _build_checkout_link_args(db, user, invoice.map_id)
            if args:
                await db.commit()
                background_tasks.add_task(_send_checkout_link_safe, *args)

    return dict(_RESEND_CLAIM_ACCEPTED)


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
    s = settings.STRIPE_WEBHOOK_SECRET or ""
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

        checkout_link_args = None
        created_user = False

        if not user_id:
            if event_type != "checkout.session.completed":
                logger.info(f"Ignoring {event_type} for guest session with no prior user: {session_obj['id']}")
                return {"status": "ignored", "reason": "guest session incomplete"}

            email = await _resolve_email(session_obj)
            if not email:
                logger.error(f"PAID GUEST CHECKOUT WITH NO EMAIL, needs manual fix: {session_obj['id']}")
                return {"status": "ignored", "reason": "no email on guest session"}

            guest_user, created_user = await crud.users.get_or_create_pending_user(db, email)
            user_id = guest_user.id
            logger.info(f"Resolved guest email={_mask_email(email)} to user_id={user_id} created={created_user}")

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
                created_user=created_user,
                checkout_nonce_hash=_field(metadata, "checkout_nonce_hash") or None,
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
        inactive_account = False

        if event_type == "checkout.session.completed":
            owner = await crud.users.get_user_by_id(db, user_id_int)
            if owner is not None and not owner.is_active:
                # Deactivated accounts can't log in, so granting access would
                # leave the buyer charged and locked out. Refund instead.
                inactive_account = True
                invoice.status = "refunded"
                invoice.failure_reason = "Account inactive; auto-refunded"
                logger.warning(
                    f"PAID CHECKOUT FOR INACTIVE ACCOUNT: user={user_id_int} "
                    f"map={map_id_int} session={session_id}"
                )

        if event_type == "checkout.session.completed" and not inactive_account:
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

            if not duplicate_purchase:
                user = await crud.users.get_user_by_id(db, user_id_int)
                if user:
                    # One email per purchase: a sign-in link for passwordless
                    # buyers (also covers auto-logged-in guests: receipt and a
                    # way back in from another device). Nothing for password users.
                    checkout_link_args = await _build_checkout_link_args(db, user, map_id_int)

        await db.commit()
        logger.info(f"Webhook committed successfully: session={session_id} status={final_status}")
        
        if duplicate_purchase:
            await _refund_duplicate_purchase(payment_intent_id, session_id, user_id_int, map_id_int)
        elif inactive_account:
            await _refund_duplicate_purchase(
                payment_intent_id, session_id, user_id_int, map_id_int, reason="requested_by_customer"
            )

        if checkout_link_args:
            await _send_checkout_link_safe(*checkout_link_args)

        if duplicate_purchase:
            return {"status": "duplicate_refunded"}
        if inactive_account:
            return {"status": "inactive_refunded"}
        return {"status": final_status}

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