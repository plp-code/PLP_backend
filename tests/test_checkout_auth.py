"""Part 1: guest checkout auto-login, claim emails, claim token TTL, resend-claim."""
import asyncio
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest
from sqlalchemy import select

from conftest import (
    API, cookie_header, cookie_value, deliver_webhook, set_cookie_names, start_checkout,
)
from src.python.app import crud
from src.python.app.core import jwt as jwt_module
from src.python.app.core.config import settings
from src.python.app.core.security import hash_password
from src.python.app.models import Invoice, Token, User

pytestmark = pytest.mark.anyio

ALLOWED_REQUIRES_LOGIN_KEYS = {"status", "map_slug", "requires_login", "email_hint"}


async def _guest_purchase(make_client, fake_stripe, email):
    """Guest starts checkout in `browser`, Stripe calls the webhook."""
    browser = make_client()
    stripe_session = await start_checkout(browser, fake_stripe)
    assert stripe_session["metadata"]["user_id"] == ""
    await deliver_webhook(make_client(), stripe_session, email)
    return browser, stripe_session["id"]


async def _poll(client, session_id, **kwargs):
    resp = await client.get(f"{API}/checkout/status/{session_id}", **kwargs)
    assert resp.status_code == 200, resp.text
    return resp


async def _user(db_session, email) -> User:
    async with db_session() as db:
        return await crud.users.get_user_by_email(db, email)


# ── 1c: brand-new email ──────────────────────────────────────────────────────

async def test_new_guest_email_mints_one_access_only_24h_session(make_client, fake_stripe, db_session):
    browser, session_id = await _guest_purchase(make_client, fake_stripe, "newbuyer@example.com")

    first = await _poll(browser, session_id)
    assert first.json() == {"status": "complete", "map_slug": "test-map"}
    names = set_cookie_names(first)
    assert "access_token" in names
    assert "refresh_token" not in names

    token = cookie_value(first, "access_token")
    payload = pyjwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    lifetime = payload["exp"] - datetime.now(timezone.utc).timestamp()
    assert timedelta(hours=23, minutes=55).total_seconds() < lifetime <= timedelta(hours=24).total_seconds()
    assert "Max-Age=86400" in cookie_header(first, "access_token")

    me = await browser.get(f"{API}/users/me")
    assert me.status_code == 200
    assert me.json()["email"] == "newbuyer@example.com"

    async with db_session() as db:
        tokens = (await db.execute(select(Token))).scalars().all()
    assert tokens == [], "no refresh token may be stored for a passwordless guest"

    # A second poll from a browser without the access cookie gets nothing.
    second_browser = make_client()
    second_browser.cookies.set("checkout_nonce", browser.cookies.get("checkout_nonce"))
    second = await _poll(second_browser, session_id)
    assert set_cookie_names(second) == []
    assert second.json()["requires_login"] is True


# ── 1c: email already has a row ──────────────────────────────────────────────

async def _seed_user(db_session, email, *, password, verified):
    async with db_session() as db:
        if password is None:
            user, created = await crud.users.get_or_create_pending_user(db, email)
            assert created
        else:
            user = await crud.users.create_user(
                db, email=email, first_name="Vic", last_name="Tim",
                hashed_password=hash_password(password),
            )
        user.is_verified = verified
        user.reset_jti = "pre-existing-jti"
        await db.commit()


@pytest.mark.parametrize(
    "password,verified,expect_claim_email",
    [
        (None, False, True),           # pending guest/waitlist row
        ("hunter22hunter22", False, False),  # registered, unverified
        ("hunter22hunter22", True, False),   # registered, verified
    ],
    ids=["pending", "unverified-with-password", "verified-with-password"],
)
async def test_existing_email_never_gets_cookies(
    make_client, fake_stripe, db_session, outbox, password, verified, expect_claim_email,
):
    email = "victim@example.com"
    await _seed_user(db_session, email, password=password, verified=verified)

    # Victim already owns another map (their data an attacker must not reach).
    async with db_session() as db:
        victim = await crud.users.get_user_by_email(db, email)
        other_map = await crud.maps.get_map_by_slug(db, "other-map")
        inv = await crud.invoices.create_invoice(
            db, user_id=victim.id, map_id=other_map.id,
            stripe_checkout_session_id="cs_victim_old", amount=700, status="paid",
        )
        await crud.purchases.create_purchase(db, user_id=victim.id, map_id=other_map.id, invoice_id=inv.id)
        await db.commit()

    browser, session_id = await _guest_purchase(make_client, fake_stripe, email)
    resp = await _poll(browser, session_id)

    assert set_cookie_names(resp) == []
    body = resp.json()
    assert body["status"] == "complete"
    assert body["requires_login"] is True
    assert body["email_hint"] == "v***@example.com"
    assert set(body) <= ALLOWED_REQUIRES_LOGIN_KEYS
    assert "other-map" not in resp.text
    assert (await browser.get(f"{API}/users/me")).status_code == 401

    after = await _user(db_session, email)
    assert outbox.of_kind("reset") == [], "never a set-password email after checkout"
    assert after.reset_jti == "pre-existing-jti"
    if expect_claim_email:
        # Passwordless: exactly one email, a 60-minute sign-in link to the map.
        assert len(outbox.sent) == 1
        (mail,) = outbox.of_kind("checkout_magic")
        assert mail.to == email
        assert mail.return_to == "/maps/test-map"
        assert mail.map_name == "Test Map"
        assert mail.valid_for == "60 minutes"
        assert after.magic_link_jti is not None
    else:
        # Has a password: nothing sent, no jti touched.
        assert outbox.sent == []
        assert after.magic_link_jti is None


async def test_pending_row_with_no_other_activity_still_not_minted(make_client, fake_stripe, db_session):
    """created_user is what matters: a waitlist row created earlier is not this invoice's."""
    async with db_session() as db:
        await crud.users.get_or_create_pending_user(db, "waitlister@example.com")
        await db.commit()

    browser, session_id = await _guest_purchase(make_client, fake_stripe, "waitlister@example.com")
    resp = await _poll(browser, session_id)
    assert set_cookie_names(resp) == []
    assert resp.json()["requires_login"] is True

    async with db_session() as db:
        invoice = await crud.invoices.get_by_session_id(db, session_id)
    assert invoice.created_user is False


# ── 1d: browser binding ──────────────────────────────────────────────────────

async def test_missing_nonce_gets_no_cookies(make_client, fake_stripe):
    _, session_id = await _guest_purchase(make_client, fake_stripe, "fresh1@example.com")
    stranger = make_client()  # has the session_id URL, not the cookie
    resp = await _poll(stranger, session_id)
    assert set_cookie_names(resp) == []
    assert resp.json()["requires_login"] is True


async def test_mismatched_nonce_gets_no_cookies(make_client, fake_stripe):
    _, session_id = await _guest_purchase(make_client, fake_stripe, "fresh2@example.com")
    stranger = make_client()
    stranger.cookies.set("checkout_nonce", "not-the-real-nonce")
    resp = await _poll(stranger, session_id)
    assert set_cookie_names(resp) == []
    assert resp.json()["requires_login"] is True


async def test_nonce_cookie_is_httponly_lax_and_scoped(make_client):
    resp = await make_client().post(f"{API}/checkout/create-session", params={"map_slug": "test-map"})
    header = cookie_header(resp, "checkout_nonce").lower()
    assert "httponly" in header
    assert "samesite=lax" in header
    assert "path=/api/v1/checkout" in header


async def test_only_hash_of_nonce_leaves_server(make_client, fake_stripe):
    browser = make_client()
    stripe_session = await start_checkout(browser, fake_stripe)
    raw = browser.cookies.get("checkout_nonce")
    assert raw and raw not in str(stripe_session)
    assert len(stripe_session["metadata"]["checkout_nonce_hash"]) == 64


# ── 1c: once-only under concurrency ──────────────────────────────────────────

async def test_two_concurrent_polls_mint_only_one_session(make_client, fake_stripe, db_session):
    browser, session_id = await _guest_purchase(make_client, fake_stripe, "racer@example.com")
    nonce = browser.cookies.get("checkout_nonce")
    tab_a, tab_b = make_client(), make_client()
    for tab in (tab_a, tab_b):
        tab.cookies.set("checkout_nonce", nonce)

    responses = await asyncio.gather(
        tab_a.get(f"{API}/checkout/status/{session_id}"),
        tab_b.get(f"{API}/checkout/status/{session_id}"),
    )
    assert [r.status_code for r in responses] == [200, 200]
    minted = [r for r in responses if "access_token" in set_cookie_names(r)]
    assert len(minted) == 1

    async with db_session() as db:
        invoice = await crud.invoices.get_by_session_id(db, session_id)
    assert invoice.session_minted_at is not None


# ── logged-in purchase ───────────────────────────────────────────────────────

async def test_logged_in_purchase_completes_without_new_cookies(make_client, fake_stripe, db_session, outbox):
    client = make_client()
    reg = await client.post(f"{API}/auth/register", json={
        "email": "member@example.com", "first_name": "Mem", "last_name": "Ber",
        "password": "correct-horse-battery",
    })
    assert reg.status_code == 201

    # Registered but unverified, with a pending forgot-password link.
    async with db_session() as db:
        user = await crud.users.get_user_by_email(db, "member@example.com")
        user.reset_jti = "forgot-password-jti"
        await db.commit()

    stripe_session = await start_checkout(client, fake_stripe)
    assert stripe_session["metadata"]["user_id"] == str(user.id)
    await deliver_webhook(make_client(), stripe_session, "member@example.com")

    resp = await _poll(client, stripe_session["id"])
    assert resp.json() == {"status": "complete", "map_slug": "test-map"}
    assert set_cookie_names(resp) == []

    # User has a password: no checkout email of any kind, no jti touched.
    assert outbox.of_kind("reset") == []
    assert outbox.of_kind("checkout_magic") == []
    after = await _user(db_session, "member@example.com")
    assert after.reset_jti == "forgot-password-jti"
    assert after.magic_link_jti is None


# ── 2: build_claim_email_args ────────────────────────────────────────────────

async def test_build_claim_email_args_skips_password_users(db_session):
    async with db_session() as db:
        user = await crud.users.create_user(
            db, email="haspw@example.com", first_name="A", last_name="B",
            hashed_password=hash_password("whatever-password"),
        )
        user.reset_jti = "keep-me"
        await db.flush()
        assert await crud.users.build_claim_email_args(db, user) is None
        await db.commit()
    assert (await _user(db_session, "haspw@example.com")).reset_jti == "keep-me"


async def test_build_claim_email_args_covers_verified_passwordless(db_session):
    async with db_session() as db:
        user, _ = await crud.users.get_or_create_pending_user(db, "magic@example.com")
        user.is_verified = True
        await db.flush()
        args = await crud.users.build_claim_email_args(db, user)
        await db.commit()
    assert args is not None and args[0] == "magic@example.com"


# ── 3: claim token lifetime ──────────────────────────────────────────────────

def _issued_ago(monkeypatch, ago: timedelta):
    real = datetime

    class ShiftedDatetime(real):
        @classmethod
        def now(cls, tz=None):
            return real.now(tz) - ago

    monkeypatch.setattr(jwt_module, "datetime", ShiftedDatetime)


@pytest.mark.parametrize(
    "ttl,age,valid",
    [
        (jwt_module.CLAIM_TOKEN_TTL, timedelta(hours=23), True),
        (jwt_module.CLAIM_TOKEN_TTL, timedelta(hours=25), False),
        (jwt_module.PASSWORD_RESET_TOKEN_TTL, timedelta(minutes=14), True),
        (jwt_module.PASSWORD_RESET_TOKEN_TTL, timedelta(minutes=16), False),
    ],
    ids=["claim-23h", "claim-25h", "forgot-14m", "forgot-16m"],
)
async def test_token_lifetimes(monkeypatch, ttl, age, valid):
    _issued_ago(monkeypatch, age)
    token, _ = jwt_module.create_password_reset_token("x@example.com", ttl=ttl)
    monkeypatch.undo()
    if valid:
        assert jwt_module.decode_password_reset_token(token)["email"] == "x@example.com"
    else:
        with pytest.raises(pyjwt.InvalidTokenError):
            jwt_module.decode_password_reset_token(token)


def _lifetime(token: str) -> float:
    payload = pyjwt.decode(token, options={"verify_signature": False})
    return payload["exp"] - datetime.now(timezone.utc).timestamp()


async def test_forgot_password_link_is_still_15_minutes(make_client, db_session, outbox):
    async with db_session() as db:
        await crud.users.create_user(
            db, email="forgetful@example.com", first_name="F", last_name="G",
            hashed_password=hash_password("old-password-123"),
        )
        await db.commit()
    resp = await make_client().post(f"{API}/auth/forgot-password", json={"email": "forgetful@example.com"})
    assert resp.status_code == 200
    (mail,) = outbox.of_kind("reset")
    assert mail.valid_for == "15 minutes"
    assert 14 * 60 < _lifetime(mail.token) <= 15 * 60


async def test_claim_token_is_24h_single_use_and_revokes_sessions(make_client, db_session):
    # build_claim_email_args no longer has a caller after the switch to magic
    # links; the token mechanism is kept and still tested.
    async with db_session() as db:
        user, _ = await crud.users.get_or_create_pending_user(db, "claimer@example.com")
        _, claim_token = await crud.users.build_claim_email_args(db, user)
        await db.commit()
    assert 23.9 * 3600 < _lifetime(claim_token) <= 24 * 3600

    async with db_session() as db:
        await crud.tokens.store_refresh_token(
            db, user_id=user.id, token="stale-refresh",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await db.commit()

    client = make_client()
    ok = await client.post(f"{API}/auth/reset-password", json={"token": claim_token, "new_password": "brand-new-pass"})
    assert ok.status_code == 200
    assert "refresh_token" in set_cookie_names(ok), "refresh token is issued once a password is set"

    again = await make_client().post(f"{API}/auth/reset-password", json={"token": claim_token, "new_password": "another-pass-1"})
    assert again.status_code == 400

    async with db_session() as db:
        stale = await crud.tokens.validate_refresh_token(db, "stale-refresh")
        claimed = await crud.users.get_user_by_id(db, user.id)
    assert stale is None
    assert claimed.is_verified and claimed.reset_jti is None


# ── 1e: resend-claim ─────────────────────────────────────────────────────────

async def test_resend_claim_is_identical_for_every_case(make_client, fake_stripe, db_session, outbox):
    _, guest_session = await _guest_purchase(make_client, fake_stripe, "pendingbuyer@example.com")

    member = make_client()
    await member.post(f"{API}/auth/register", json={
        "email": "pwholder@example.com", "first_name": "P", "last_name": "W",
        "password": "a-real-password",
    })
    member_checkout = await start_checkout(member, fake_stripe)
    await deliver_webhook(make_client(), member_checkout, "pwholder@example.com")

    (first_mail,) = outbox.of_kind("checkout_magic")
    outbox.sent.clear()
    reset_before = (await _user(db_session, "pendingbuyer@example.com")).reset_jti

    responses = {}
    for label, sid in [
        ("existing-passwordless", guest_session),
        ("nonexistent", "cs_does_not_exist"),
        ("password-holder", member_checkout["id"]),
    ]:
        responses[label] = await make_client().post(f"{API}/checkout/resend-claim", json={"session_id": sid})

    statuses = {label: r.status_code for label, r in responses.items()}
    assert set(statuses.values()) == {202}, statuses
    bodies = {r.content for r in responses.values()}
    assert len(bodies) == 1, bodies

    assert outbox.of_kind("reset") == []
    sent = outbox.of_kind("checkout_magic")
    assert [m.to for m in sent] == ["pendingbuyer@example.com"]
    assert sent[0].valid_for == "60 minutes"
    assert (await _user(db_session, "pendingbuyer@example.com")).reset_jti == reset_before

    # The newer link replaces the older one: old fails, new works.
    old = await make_client().post(f"{API}/auth/verify-magic-link", json={"token": first_mail.token})
    assert old.status_code == 400
    new = await make_client().post(f"{API}/auth/verify-magic-link", json={"token": sent[0].token})
    assert new.status_code == 200
    assert new.json()["return_to"] == "/maps/test-map"


async def test_resend_claim_per_session_limit_is_silent(make_client, fake_stripe, outbox):
    _, session_id = await _guest_purchase(make_client, fake_stripe, "spammed@example.com")
    outbox.sent.clear()
    client = make_client()
    bodies = set()
    for _ in range(5):
        r = await client.post(f"{API}/checkout/resend-claim", json={"session_id": session_id})
        assert r.status_code == 202
        bodies.add(r.content)
    assert len(bodies) == 1
    assert len(outbox.of_kind("checkout_magic")) == 3  # RESEND_CLAIM_PER_SESSION_LIMIT
    assert outbox.of_kind("reset") == []


# ── 4: review author fallback ────────────────────────────────────────────────

async def test_review_author_anonymous_when_unnamed():
    from types import SimpleNamespace
    from src.python.app.schemas.review import ReviewAuthor

    unnamed = ReviewAuthor.model_validate(
        SimpleNamespace(first_name=None, last_name=None, email="secret.person@example.com")
    ).model_dump()
    assert unnamed == {"first_name": "Anonymous", "last_initial": None}
    assert "secret" not in str(unnamed)

    named = ReviewAuthor.model_validate(SimpleNamespace(first_name="Jane", last_name="smith")).model_dump()
    assert named == {"first_name": "Jane", "last_initial": "S"}
