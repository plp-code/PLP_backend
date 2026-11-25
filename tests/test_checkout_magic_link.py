"""Checkout sign-in email: magic link to the bought map, returnTo safety, has_password."""
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

import jwt as pyjwt
import pytest

from conftest import API, deliver_webhook, set_cookie_names, start_checkout
from src.python.app import crud
from src.python.app.core import email as email_module
from src.python.app.crud.auth import DEFAULT_RETURN_PATH, safe_return_path

pytestmark = pytest.mark.anyio


async def _guest_buys(make_client, fake_stripe, email):
    browser = make_client()
    stripe_session = await start_checkout(browser, fake_stripe)
    await deliver_webhook(make_client(), stripe_session, email)
    return browser, stripe_session["id"]


async def _user(db_session, email):
    async with db_session() as db:
        return await crud.users.get_user_by_email(db, email)


# ── which email ──────────────────────────────────────────────────────────────

async def test_auto_logged_in_guest_gets_magic_link_and_no_set_password(make_client, fake_stripe, db_session, outbox):
    browser, session_id = await _guest_buys(make_client, fake_stripe, "brandnew@example.com")
    status = await browser.get(f"{API}/checkout/status/{session_id}")
    assert "access_token" in set_cookie_names(status), "precondition: guest was auto-logged-in"

    assert len(outbox.sent) == 1
    (mail,) = outbox.of_kind("checkout_magic")
    assert mail.to == "brandnew@example.com"
    assert mail.return_to == "/maps/test-map"
    assert outbox.of_kind("reset") == []
    assert (await _user(db_session, "brandnew@example.com")).reset_jti is None


async def test_checkout_link_lifetime_is_60_minutes(make_client, fake_stripe, outbox):
    await _guest_buys(make_client, fake_stripe, "timer@example.com")
    (mail,) = outbox.of_kind("checkout_magic")
    payload = pyjwt.decode(mail.token, options={"verify_signature": False})
    remaining = payload["exp"] - datetime.now(timezone.utc).timestamp()
    assert 59 * 60 < remaining <= 60 * 60
    assert payload["type"] == "magic"
    assert payload["return_to"] == "/maps/test-map"


async def test_login_page_magic_link_still_20_minutes(make_client, db_session, outbox):
    async with db_session() as db:
        await crud.users.get_or_create_pending_user(db, "loginpage@example.com")
        await db.commit()
    await make_client().post(f"{API}/auth/magic-link", json={"email": "loginpage@example.com"})
    (mail,) = outbox.of_kind("magic")
    payload = pyjwt.decode(mail.token, options={"verify_signature": False})
    remaining = payload["exp"] - datetime.now(timezone.utc).timestamp()
    assert 19 * 60 < remaining <= 20 * 60
    assert "return_to" not in payload


# ── single use, verification, landing page ───────────────────────────────────

async def test_magic_link_single_use_verifies_and_lands_on_map(make_client, fake_stripe, db_session, outbox):
    await _guest_buys(make_client, fake_stripe, "lander@example.com")
    (mail,) = outbox.of_kind("checkout_magic")
    assert (await _user(db_session, "lander@example.com")).is_verified is False

    first = await make_client().post(f"{API}/auth/verify-magic-link", json={"token": mail.token})
    assert first.status_code == 200
    assert first.json() == {"status": "logged_in", "return_to": "/maps/test-map"}
    assert "access_token" in set_cookie_names(first)

    user = await _user(db_session, "lander@example.com")
    assert user.is_verified is True
    assert user.magic_link_jti is None

    second = await make_client().post(f"{API}/auth/verify-magic-link", json={"token": mail.token})
    assert second.status_code == 400


@pytest.mark.parametrize(
    "bad",
    ["//evil.com", "https://evil.com", "/\\evil.com", "\\\\evil.com", "/\t/evil.com",
     "javascript:alert(1)", "maps/x", "", None, 42],
    ids=["scheme-relative", "absolute", "slash-backslash", "backslashes", "tab-smuggle",
         "javascript", "no-leading-slash", "empty", "none", "not-a-string"],
)
async def test_unsafe_return_to_falls_back_to_default(make_client, db_session, bad):
    # Simulate a token whose return_to claim is unsafe; the consuming endpoint
    # must not pass it through even though the token itself is valid.
    async with db_session() as db:
        user, _ = await crud.users.get_or_create_pending_user(db, "redirect@example.com")
        token = await crud.auth.create_magic_link_token(db, user.id, return_to=bad)
        await db.commit()
    resp = await make_client().post(f"{API}/auth/verify-magic-link", json={"token": token})
    assert resp.status_code == 200
    assert resp.json()["return_to"] == DEFAULT_RETURN_PATH


async def test_safe_return_path_allows_relative_map_paths():
    assert safe_return_path("/maps/los-angeles-ca") == "/maps/los-angeles-ca"
    assert safe_return_path("/maps/x?tab=list") == "/maps/x?tab=list"
    assert DEFAULT_RETURN_PATH == "/maps"


# ── email content ────────────────────────────────────────────────────────────

async def test_checkout_email_content(monkeypatch):
    captured = {}
    monkeypatch.setattr(email_module.resend.Emails, "send", lambda params: captured.update(params))
    await email_module.send_checkout_magic_link_email(
        "buyer@example.com", "tok123", map_name="Los Angeles <CA>",
        return_to="/maps/los-angeles-ca", valid_for="60 minutes",
    )
    html = captured["html"]
    assert captured["subject"] == "Your map is ready"
    assert "Open my map" in html
    assert "Los Angeles &lt;CA&gt;" in html and "<CA>" not in html
    assert "60 minutes" in html and "used once" in html
    assert "Didn't buy this? You can ignore this email." in html
    assert "http://frontend.test/forgot-password" in html
    assert "set your password" not in html.lower()

    link = html.split('href="', 1)[1].split('"', 1)[0]
    query = parse_qs(urlsplit(link).query)
    assert urlsplit(link).path == "/magic-login"
    assert query == {"token": ["tok123"], "returnTo": ["/maps/los-angeles-ca"]}
    # One token only: every occurrence is part of the same sign-in link
    # (button href, fallback href, fallback text). No second token anywhere.
    assert html.count("tok123") == html.count(link) == 3


# ── has_password on /users/me ────────────────────────────────────────────────

async def test_has_password_false_for_pending_true_after_claim(make_client, fake_stripe, db_session, outbox):
    await _guest_buys(make_client, fake_stripe, "banner@example.com")
    (mail,) = outbox.of_kind("checkout_magic")

    client = make_client()
    assert (await client.post(f"{API}/auth/verify-magic-link", json={"token": mail.token})).status_code == 200
    me = (await client.get(f"{API}/users/me")).json()
    assert me["has_password"] is False
    assert "hashed_password" not in me and not any("$2b$" in str(v) for v in me.values())

    await make_client().post(f"{API}/auth/forgot-password", json={"email": "banner@example.com"})
    (reset,) = outbox.of_kind("reset")
    claimed = make_client()
    ok = await claimed.post(f"{API}/auth/reset-password", json={"token": reset.token, "new_password": "now-with-password"})
    assert ok.status_code == 200
    me = (await claimed.get(f"{API}/users/me")).json()
    assert me["has_password"] is True
    assert "hashed_password" not in me
