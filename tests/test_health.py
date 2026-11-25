import uuid

import pytest

from models.orm import User
from utils.jwt import create_access_token
from utils.security import hash_password


def test_read_root(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Recruitment & Hiring API is running"
    }


def test_metrics_unauthorized(client):
    response = client.get("/metrics")
    assert response.status_code == 401


@pytest.mark.parametrize(
    "role, expected_status",
    [
        ("candidate", 403),
        ("admin", 403),
        ("super_admin", 200),
    ],
)
def test_metrics_role_access(client, db_session, role, expected_status):
    user = User(
        full_name=f"Test {role}",
        email=f"{role}_metrics@example.com",
        hashed_password=hash_password("password123"),
        role=role,
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role,
    })

    response = client.get(
        "/metrics",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == expected_status


def test_request_id_preserves_valid_uuid(client):
    request_id = str(uuid.uuid4())

    response = client.get(
        "/health",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_request_id_replaces_invalid_value(client):
    response = client.get(
        "/health",
        headers={"X-Request-ID": "invalid request id!"}
    )

    assert response.status_code == 200

    generated_id = response.headers["X-Request-ID"]

    assert generated_id != "invalid request id!"
    uuid.UUID(generated_id)
