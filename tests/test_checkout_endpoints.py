from types import SimpleNamespace

from app.core.security import get_password_hash
from app.db.models import Map, User, UserMapAccess


def _login(client, email: str, password: str):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200


def test_create_checkout_session_requires_auth(client):
    response = client.post("/api/v1/checkout/create-session", json={"map_id": 1})

    assert response.status_code == 401


def test_create_checkout_session_map_not_found(client, db_session):
    user = User(
        email="buyer@example.com",
        first_name="Buyer",
        last_name="User",
        hashed_password=get_password_hash("BuyerPass123!"),
    )
    db_session.add(user)
    db_session.commit()

    _login(client, "buyer@example.com", "BuyerPass123!")

    response = client.post("/api/v1/checkout/create-session", json={"map_id": 9999})

    assert response.status_code == 404
    assert response.json()["detail"] == "Map not found"


def test_create_checkout_session_success(client, db_session, monkeypatch):
    user = User(
        email="checkout@example.com",
        first_name="Checkout",
        last_name="User",
        hashed_password=get_password_hash("CheckoutPass123!"),
    )
    map_item = Map(
        title="Berlin",
        slug="berlin",
        description="Berlin map",
        region="DE",
        map_price=4500,
    )
    db_session.add_all([user, map_item])
    db_session.commit()

    _login(client, "checkout@example.com", "CheckoutPass123!")

    def fake_create(**kwargs):
        return SimpleNamespace(url="https://checkout.stripe.test/session_123")

    monkeypatch.setattr("app.api.v1.endpoints.checkout.stripe.checkout.Session.create", fake_create)

    response = client.post("/api/v1/checkout/create-session", json={"map_id": map_item.id})

    assert response.status_code == 200
    assert response.json()["url"] == "https://checkout.stripe.test/session_123"


def test_webhook_invalid_payload_returns_400(client, monkeypatch):
    def fake_construct_event(payload, sig_header, secret):
        raise ValueError("bad payload")

    monkeypatch.setattr("app.api.v1.endpoints.checkout.stripe.Webhook.construct_event", fake_construct_event)

    response = client.post(
        "/api/v1/checkout/webhook",
        content=b"not-json",
        headers={"stripe-signature": "sig_test"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid payload"


def test_webhook_checkout_completed_grants_map_access(client, db_session, monkeypatch):
    user = User(
        email="webhook@example.com",
        first_name="Web",
        last_name="Hook",
        hashed_password=get_password_hash("WebhookPass123!"),
    )
    map_item = Map(
        title="Madrid",
        slug="madrid",
        description="Madrid map",
        region="ES",
        map_price=3600,
    )
    db_session.add_all([user, map_item])
    db_session.commit()

    def fake_construct_event(payload, sig_header, secret):
        return {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {
                        "user_id": str(user.id),
                        "map_id": str(map_item.id),
                    }
                }
            },
        }

    monkeypatch.setattr("app.api.v1.endpoints.checkout.stripe.Webhook.construct_event", fake_construct_event)

    response = client.post(
        "/api/v1/checkout/webhook",
        content=b"{}",
        headers={"stripe-signature": "sig_ok"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"

    access = (
        db_session.query(UserMapAccess)
        .filter(UserMapAccess.user_id == user.id, UserMapAccess.map_id == map_item.id)
        .first()
    )
    assert access is not None
