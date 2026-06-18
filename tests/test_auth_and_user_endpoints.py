from app.core.security import get_password_hash
from app.db.models import User


def test_register_user_success(client, db_session):
    payload = {
        "email": "newuser@example.com",
        "password": "StrongPass123!",
        "first_name": "New",
        "last_name": "User",
    }

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    assert response.json()["message"] == "User registered successfully"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies

    user = db_session.query(User).filter(User.email == payload["email"]).first()
    assert user is not None


def test_register_duplicate_email_fails(client, db_session):
    user = User(
        email="dupe@example.com",
        first_name="Dupe",
        last_name="User",
        hashed_password=get_password_hash("Password123!"),
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "dupe@example.com",
            "password": "AnotherPass123!",
            "first_name": "Another",
            "last_name": "User",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login_success_sets_auth_cookies(client, db_session):
    user = User(
        email="login@example.com",
        first_name="Log",
        last_name="In",
        hashed_password=get_password_hash("Secret123!"),
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "Secret123!"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Logged in"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_login_invalid_credentials(client, db_session):
    user = User(
        email="badlogin@example.com",
        first_name="Bad",
        last_name="Login",
        hashed_password=get_password_hash("CorrectPass123!"),
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "badlogin@example.com", "password": "WrongPass123!"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_get_current_user_profile_requires_auth(client):
    response = client.get("/api/v1/user/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_get_current_user_profile_after_login(client, db_session):
    user = User(
        email="profile@example.com",
        first_name="Profile",
        last_name="Tester",
        hashed_password=get_password_hash("ProfilePass123!"),
    )
    db_session.add(user)
    db_session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "profile@example.com", "password": "ProfilePass123!"},
    )
    assert login_response.status_code == 200

    me_response = client.get("/api/v1/user/me")

    assert me_response.status_code == 200
    payload = me_response.json()
    assert payload["email"] == "profile@example.com"
    assert payload["first_name"] == "Profile"
    assert payload["last_name"] == "Tester"
