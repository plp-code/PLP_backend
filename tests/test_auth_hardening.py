"""Part 2: bcrypt 72-byte limit, /register race, rate-limit client IP, per-email login cap."""
import httpx
import pytest
from fastapi import FastAPI
from starlette.requests import Request

from conftest import API
from src.python.app import crud
from src.python.app.core import rate_limit
from src.python.app.core.config import settings
from src.python.app.core.security import hash_password, verify_password
from src.python.app.routes import auth as auth_routes

pytestmark = pytest.mark.anyio

LONG_ASCII = "a" * 73             # 73 chars, 73 bytes
MULTIBYTE_OVER = "é" * 40         # 40 chars, 80 bytes: passes max_length, fails bytes
MULTIBYTE_OK = "é" * 36           # 36 chars, exactly 72 bytes


# ── 6: passwords over 72 bytes ───────────────────────────────────────────────

@pytest.mark.parametrize("password", [LONG_ASCII, MULTIBYTE_OVER], ids=["ascii-73", "utf8-80-bytes"])
async def test_register_rejects_over_72_bytes(make_client, password):
    resp = await make_client().post(f"{API}/auth/register", json={
        "email": "long@example.com", "first_name": "L", "last_name": "P", "password": password,
    })
    assert resp.status_code == 422


async def test_register_accepts_exactly_72_bytes(make_client):
    resp = await make_client().post(f"{API}/auth/register", json={
        "email": "edge@example.com", "first_name": "E", "last_name": "D", "password": MULTIBYTE_OK,
    })
    assert resp.status_code == 201
    login = await make_client().post(f"{API}/auth/login", json={"email": "edge@example.com", "password": MULTIBYTE_OK})
    assert login.status_code == 200


async def test_reset_password_rejects_over_72_bytes(make_client):
    resp = await make_client().post(f"{API}/auth/reset-password", json={"token": "x", "new_password": MULTIBYTE_OVER})
    assert resp.status_code == 422


async def test_login_with_over_72_bytes_is_generic_401(make_client, db_session):
    async with db_session() as db:
        await crud.users.create_user(
            db, email="member@example.com", first_name="M", last_name="B",
            hashed_password=hash_password("normal-password"),
        )
        await db.commit()
    resp = await make_client().post(f"{API}/auth/login", json={"email": "member@example.com", "password": LONG_ASCII})
    wrong = await make_client().post(f"{API}/auth/login", json={"email": "member@example.com", "password": "wrong-password"})
    assert resp.status_code == 401
    assert resp.json() == wrong.json()


async def test_verify_password_never_raises():
    assert verify_password(LONG_ASCII, hash_password("short-one")) is False


# ── 7: concurrent /register ──────────────────────────────────────────────────

async def test_register_insert_race_returns_202(make_client, db_session, monkeypatch):
    async with db_session() as db:
        await crud.users.create_user(
            db, email="raced@example.com", first_name="R", last_name="C",
            hashed_password=hash_password("first-writer-wins"),
        )
        await db.commit()

    # Simulate losing the race: our lookup ran before the other insert committed.
    async def lookup_saw_nothing(db, email):
        return None

    monkeypatch.setattr(auth_routes.crud.users, "get_user_by_email", lookup_saw_nothing)
    resp = await make_client().post(f"{API}/auth/register", json={
        "email": "raced@example.com", "first_name": "R", "last_name": "C", "password": "second-writer",
    })
    assert resp.status_code == 202
    assert resp.json() == {"status": "check_email"}
    assert resp.headers.get_list("set-cookie") == []


# ── 8: client IP for rate limiting ───────────────────────────────────────────

def _request(xff: str | None = None, peer: str = "10.0.0.1", **headers) -> Request:
    raw = [(k.replace("_", "-").encode(), v.encode()) for k, v in headers.items()]
    if xff is not None:
        raw.append((b"x-forwarded-for", xff.encode()))
    return Request({"type": "http", "headers": raw, "client": (peer, 1234)})


async def test_client_ip_ignores_spoofed_leftmost(monkeypatch):
    monkeypatch.setattr(settings, "TRUSTED_PROXY_IP_HEADER", None)
    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 1)
    # Client sent "6.6.6.6"; our proxy appended the real address.
    assert rate_limit.client_ip(_request("6.6.6.6, 203.0.113.9")) == "203.0.113.9"
    assert rate_limit.client_ip(_request("203.0.113.9")) == "203.0.113.9"
    assert rate_limit.client_ip(_request(None)) == "10.0.0.1"

    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 2)
    assert rate_limit.client_ip(_request("6.6.6.6, 203.0.113.9, 172.16.0.5")) == "203.0.113.9"

    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 0)
    assert rate_limit.client_ip(_request("6.6.6.6, 203.0.113.9")) == "10.0.0.1"


async def test_client_ip_prefers_trusted_header(monkeypatch):
    monkeypatch.setattr(settings, "TRUSTED_PROXY_IP_HEADER", "do-connecting-ip")
    req = _request("6.6.6.6", do_connecting_ip="198.51.100.7")
    assert rate_limit.client_ip(req) == "198.51.100.7"


async def test_rotating_spoofed_xff_cannot_bypass_ip_limit(monkeypatch):
    monkeypatch.setattr(settings, "TRUSTED_PROXY_IP_HEADER", None)
    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 1)
    mini = FastAPI()
    mini.add_middleware(rate_limit.RedisRateLimitMiddleware, default_limit=100, redis_enabled=False)

    @mini.post("/api/v1/auth/login")
    async def login():
        return {"ok": True}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=mini), base_url="http://test") as client:
        codes = [
            (await client.post("/api/v1/auth/login", headers={"x-forwarded-for": f"1.2.3.{i}, 203.0.113.9"})).status_code
            for i in range(7)
        ]
    assert codes == [200] * 5 + [429] * 2


# ── 8: per-email login cap ───────────────────────────────────────────────────

async def test_login_per_email_cap_survives_ip_rotation(make_client):
    codes = []
    for i in range(7):
        client = make_client(headers={"x-forwarded-for": f"198.51.100.{i}"})
        resp = await client.post(f"{API}/auth/login", json={"email": "Target@Example.com", "password": "guess-1234"})
        codes.append(resp.status_code)
    assert codes == [401] * 5 + [429] * 2

    other = await make_client().post(f"{API}/auth/login", json={"email": "someone-else@example.com", "password": "x"})
    assert other.status_code == 401
