from models.orm import User
from utils.security import hash_password


def test_candidate_registration_success(client):
    payload = {
        "full_name": "Test Candidate",
        "email": "candidate1@example.com",
        "password": "password123",
        "phone": "9876543210"
    }

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    assert response.json()["email"] == payload["email"]
    assert response.json()["full_name"] == payload["full_name"]
    assert response.json()["role"] == "candidate"
    assert response.json()["is_active"] is True
    assert "hashed_password" not in response.json()


def test_candidate_registration_duplicate_email(client):
    payload = {
        "full_name": "Test Candidate",
        "email": "duplicate@example.com",
        "password": "password123",
        "phone": "9876543210"
    }

    first_response = client.post("/api/v1/auth/register", json=payload)
    second_response = client.post("/api/v1/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email is already registered."


def test_candidate_registration_invalid_data(client):
    payload = {
        "full_name": "A",
        "email": "invalid-email",
        "password": "123",
        "phone": "123"
    }

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422


def test_login_success(client):
    payload = {
        "full_name": "Login Candidate",
        "email": "login@example.com",
        "password": "password123"
    }

    client.post("/api/v1/auth/register", json=payload)

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": payload["email"],
            "password": payload["password"]
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
    assert response.json()["token_type"] == "bearer"
    assert response.json()["role"] == "candidate"


def test_login_wrong_password(client):
    payload = {
        "full_name": "Wrong Password Candidate",
        "email": "wrongpass@example.com",
        "password": "password123"
    }

    client.post("/api/v1/auth/register", json=payload)

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": payload["email"],
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Email or Password"


def test_login_unknown_email(client):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "unknown@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Email or Password"


def test_login_inactive_user(client, db_session):
    inactive_user = User(
        full_name="Inactive Candidate",
        email="inactive@example.com",
        hashed_password=hash_password("password123"),
        role="candidate",
        is_active=False
    )

    db_session.add(inactive_user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "inactive@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "User is Inactive"


def test_get_my_account_success(client):
    payload = {
        "full_name": "Profile Candidate",
        "email": "profile@example.com",
        "password": "password123"
    }

    client.post("/api/v1/auth/register", json=payload)

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": payload["email"],
            "password": payload["password"]
        }
    )

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    assert response.json()["email"] == payload["email"]
    assert response.json()["role"] == "candidate"


def test_get_my_account_unauthorized(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_refresh_token_success(client):
    payload = {
        "full_name": "Refresh Candidate",
        "email": "refresh@example.com",
        "password": "password123"
    }

    client.post("/api/v1/auth/register", json=payload)

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": payload["email"],
            "password": payload["password"]
        }
    )

    old_refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
    assert response.json()["refresh_token"] != old_refresh_token


def test_refresh_token_reuse_rejected(client):
    payload = {
        "full_name": "Rotation Candidate",
        "email": "rotation@example.com",
        "password": "password123"
    }

    client.post("/api/v1/auth/register", json=payload)

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": payload["email"],
            "password": payload["password"]
        }
    )

    old_refresh_token = login_response.json()["refresh_token"]

    first_refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token}
    )

    second_refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token}
    )

    assert first_refresh.status_code == 200
    assert second_refresh.status_code == 401


def test_refresh_token_invalid(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.token.value"}
    )

    assert response.status_code == 401


def test_logout_success(client):
    payload = {
        "full_name": "Logout Candidate",
        "email": "logout@example.com",
        "password": "password123"
    }

    client.post("/api/v1/auth/register", json=payload)

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": payload["email"],
            "password": payload["password"]
        }
    )

    tokens = login_response.json()

    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={
            "Authorization": f"Bearer {tokens['access_token']}"
        }
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


def test_logout_without_access_token(client):
    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "invalid.token.value"}
    )

    assert response.status_code == 401


def test_logout_rejects_reused_refresh_token(client):
    payload = {
        "full_name": "Logout Reuse Candidate",
        "email": "logoutreuse@example.com",
        "password": "password123"
    }

    client.post("/api/v1/auth/register", json=payload)

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": payload["email"],
            "password": payload["password"]
        }
    )

    tokens = login_response.json()

    headers = {
        "Authorization": f"Bearer {tokens['access_token']}"
    }

    refresh_payload = {
        "refresh_token": tokens["refresh_token"]
    }

    first_response = client.post(
        "/api/v1/auth/logout",
        json=refresh_payload,
        headers=headers
    )

    second_response = client.post(
        "/api/v1/auth/logout",
        json=refresh_payload,
        headers=headers
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 401


def test_logout_revokes_access_token(client):
    payload = {
        "full_name": "Revocation Candidate",
        "email": "revocation@example.com",
        "password": "password123"
    }

    client.post("/api/v1/auth/register", json=payload)

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": payload["email"],
            "password": payload["password"]
        }
    )

    tokens = login_response.json()

    headers = {
        "Authorization": f"Bearer {tokens['access_token']}"
    }

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers=headers
    )

    assert logout_response.status_code == 200

    account_response = client.get(
        "/api/v1/auth/me",
        headers=headers
    )

    assert account_response.status_code == 401
