from app.core.security import get_password_hash
from app.db.models import Map, Store, User, UserMapAccess


def test_list_maps_anonymous_marks_no_access(client, db_session):
    db_session.add(
        Map(
            title="Tokyo",
            slug="tokyo",
            description="Tokyo map",
            region="JP",
            map_price=3900,
        )
    )
    db_session.commit()

    response = client.get("/api/v1/maps/")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["slug"] == "tokyo"
    assert payload[0]["has_access"] is False


def test_list_maps_authenticated_has_access_true(client, db_session):
    user = User(
        email="maps@example.com",
        first_name="Map",
        last_name="User",
        hashed_password=get_password_hash("MapsPass123!"),
    )
    map_item = Map(
        title="Seoul",
        slug="seoul",
        description="Seoul map",
        region="KR",
        map_price=2900,
    )
    db_session.add_all([user, map_item])
    db_session.commit()

    db_session.add(UserMapAccess(user_id=user.id, map_id=map_item.id))
    db_session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "maps@example.com", "password": "MapsPass123!"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/maps/")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["slug"] == "seoul"
    assert payload[0]["has_access"] is True


def test_get_map_stores_requires_access(client, db_session):
    user = User(
        email="denied@example.com",
        first_name="Denied",
        last_name="User",
        hashed_password=get_password_hash("DeniedPass123!"),
    )
    map_item = Map(
        title="Paris",
        slug="paris",
        description="Paris map",
        region="FR",
        map_price=4900,
    )
    db_session.add_all([user, map_item])
    db_session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "denied@example.com", "password": "DeniedPass123!"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/maps/paris/stores")

    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied"


def test_get_map_stores_with_access_and_pagination(client, db_session):
    user = User(
        email="allowed@example.com",
        first_name="Allowed",
        last_name="User",
        hashed_password=get_password_hash("AllowedPass123!"),
    )
    map_item = Map(
        title="NYC",
        slug="nyc",
        description="NYC map",
        region="US",
        map_price=5900,
    )
    db_session.add_all([user, map_item])
    db_session.commit()

    db_session.add(UserMapAccess(user_id=user.id, map_id=map_item.id))
    db_session.commit()

    stores = [
        Store(
            map_id=map_item.id,
            store_name=f"Store {i}",
            address=f"{i} Main St",
            latitude=40.0 + i,
            longitude=-73.0 - i,
            is_active=True,
        )
        for i in range(1, 6)
    ]
    db_session.add_all(stores)
    db_session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "allowed@example.com", "password": "AllowedPass123!"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/maps/nyc/stores?page=1&limit=2")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert payload[0]["store_name"] == "Store 1"
    assert payload[1]["store_name"] == "Store 2"
