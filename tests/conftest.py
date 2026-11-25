"""Test harness for the auth and checkout flows.

Safety: every setting that could reach a real service is overridden here,
BEFORE the app is imported. Environment variables take precedence over .env in
pydantic-settings, so the .env DATABASE_URL, Stripe keys and Resend key are
never used. Stripe and email calls are monkeypatched; nothing leaves the process.
"""
import json
import os
import sys
import tempfile
from types import SimpleNamespace

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

_TMP_DIR = tempfile.mkdtemp(prefix="plp-tests-")
os.environ.update(
    DATABASE_URL=f"sqlite+aiosqlite:///{_TMP_DIR}/test.db",
    DB_SSL_REQUIRED="false",
    ENVIRONMENT="test",
    RATE_LIMIT_ENABLED="false",
    REDIS_ENABLED="false",
    SECRET_KEY="test-secret-key-that-is-at-least-32-characters-long",
    STRIPE_SECRET_KEY="sk_test_dummy_never_used",
    STRIPE_WEBHOOK_SECRET="whsec_dummy_never_used",
    RESEND_API_KEY="re_dummy_never_used",
    EMAIL_FROM="test@example.com",
    GOOGLE_PLACES_API_KEY="dummy",
    FRONTEND_URL="http://frontend.test",
)

import httpx  # noqa: E402
import stripe  # noqa: E402

from src.python.app.main import app  # noqa: E402
from src.python.app.core import rate_limit  # noqa: E402
from src.python.app.core.database import AsyncSessionLocal, Base, engine  # noqa: E402
from src.python.app.models import Map  # noqa: E402
from src.python.app.models.enums import MapStatus  # noqa: E402
from src.python.app.routes import auth as auth_routes  # noqa: E402
from src.python.app.routes import checkout as checkout_routes  # noqa: E402

assert "sqlite" in str(engine.url), "tests must never run against a real database"

API = "/api/v1"
MAP_SLUG = "test-map"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def fresh_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        db.add(Map(name="Test Map", slug=MAP_SLUG, price=500, status=MapStatus.LIVE))
        db.add(Map(name="Other Map", slug="other-map", price=700, status=MapStatus.LIVE))
        await db.commit()
    rate_limit._key_store.clear()
    yield


@pytest.fixture
def db_session():
    return AsyncSessionLocal


class Outbox:
    """Records every email the app tries to send."""

    def __init__(self):
        self.sent: list[SimpleNamespace] = []

    def of_kind(self, kind):
        return [m for m in self.sent if m.kind == kind]


@pytest.fixture(autouse=True)
def outbox(monkeypatch):
    box = Outbox()

    async def reset_email(to_email, reset_token, has_password, valid_for="15 minutes"):
        box.sent.append(SimpleNamespace(
            kind="reset", to=to_email, token=reset_token,
            has_password=has_password, valid_for=valid_for,
        ))

    async def magic_email(to_email, login_token):
        box.sent.append(SimpleNamespace(kind="magic", to=to_email, token=login_token))

    async def verify_email(to_email, verification_token):
        box.sent.append(SimpleNamespace(kind="verify", to=to_email, token=verification_token))

    async def checkout_link_email(to_email, login_token, map_name, return_to, valid_for):
        box.sent.append(SimpleNamespace(
            kind="checkout_magic", to=to_email, token=login_token,
            map_name=map_name, return_to=return_to, valid_for=valid_for,
        ))

    monkeypatch.setattr(checkout_routes, "send_checkout_magic_link_email", checkout_link_email)
    monkeypatch.setattr(auth_routes, "send_password_reset_email", reset_email)
    monkeypatch.setattr(auth_routes, "send_magic_login_email", magic_email)
    monkeypatch.setattr(auth_routes, "send_email_verification", verify_email)
    return box


class FakeStripe:
    def __init__(self):
        self.sessions: list[dict] = []

    def create_session(self, **kwargs):
        session_id = f"cs_test_{len(self.sessions) + 1}"
        self.sessions.append({"id": session_id, **kwargs})
        return SimpleNamespace(id=session_id, url=f"https://stripe.test/{session_id}")


@pytest.fixture(autouse=True)
def fake_stripe(monkeypatch):
    fake = FakeStripe()
    monkeypatch.setattr(stripe.checkout.Session, "create", fake.create_session)
    monkeypatch.setattr(
        stripe.Webhook, "construct_event",
        lambda payload, sig_header, secret: json.loads(payload),
    )
    monkeypatch.setattr(stripe.Refund, "create", lambda **kwargs: SimpleNamespace(id="re_test"))
    return fake


@pytest.fixture
def make_client():
    clients: list[httpx.AsyncClient] = []

    def _make(**kwargs) -> httpx.AsyncClient:
        client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", **kwargs
        )
        clients.append(client)
        return client

    yield _make
    # Clients hold no sockets with ASGITransport; dropping them is enough.


# ── flow helpers ─────────────────────────────────────────────────────────────

async def start_checkout(client: httpx.AsyncClient, fake_stripe: FakeStripe, slug: str = MAP_SLUG) -> dict:
    resp = await client.post(f"{API}/checkout/create-session", params={"map_slug": slug})
    assert resp.status_code == 200, resp.text
    return fake_stripe.sessions[-1]


async def deliver_webhook(
    client: httpx.AsyncClient, stripe_session: dict, email: str | None,
    event_type: str = "checkout.session.completed",
) -> httpx.Response:
    session_id = stripe_session["id"]
    event = {
        "id": f"evt_{session_id}",
        "type": event_type,
        "data": {"object": {
            "id": session_id,
            "metadata": stripe_session["metadata"],
            "customer_details": {"email": email},
            "customer_email": stripe_session.get("customer_email"),
            "customer": "cus_test",
            "payment_intent": f"pi_{session_id}",
            "amount_total": 500,
            "currency": "usd",
        }},
    }
    resp = await client.post(
        f"{API}/checkout/webhook", content=json.dumps(event),
        headers={"stripe-signature": "t=0,v1=fake"},
    )
    assert resp.status_code == 200, resp.text
    return resp


def set_cookie_names(resp: httpx.Response) -> list[str]:
    return [h.split("=", 1)[0].strip() for h in resp.headers.get_list("set-cookie")]


def cookie_header(resp: httpx.Response, name: str) -> str | None:
    for h in resp.headers.get_list("set-cookie"):
        if h.split("=", 1)[0].strip() == name:
            return h
    return None


def cookie_value(resp: httpx.Response, name: str) -> str | None:
    header = cookie_header(resp, name)
    if header is None:
        return None
    value = header.split("=", 1)[1].split(";", 1)[0].strip().strip('"')
    return value.removeprefix("Bearer ").strip()
