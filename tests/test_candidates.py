

from models.orm import User
from utils.security import hash_password


def create_candidate_token(client, email="applicant_test@example.com"):
    payload = {
        "full_name": "Test Applicant",
        "email": email,
        "password": "password123"
    }

    register_response = client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": payload["email"],
            "password": payload["password"]
        }
    )

    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def test_create_candidate_profile(client):
    candidate_token = create_candidate_token(client)

    response = client.post(
        "/api/v1/candidates/profile",
        json={
            "address": "Indore",
            "education": "MCA",
            "experience": "1 year",
            "skills": "Python, FastAPI, PostgreSQL",
            "resume_url": "https://example.com/resume.pdf"
        },
        headers={"Authorization": f"Bearer {candidate_token}"}
    )

    assert response.status_code == 201
    assert response.json()["address"] == "Indore"
    assert response.json()["education"] == "MCA"


def test_create_duplicate_candidate_profile(client):
    candidate_token = create_candidate_token(client)
    headers = {"Authorization": f"Bearer {candidate_token}"}

    payload = {
        "address": "Indore",
        "education": "MCA",
        "experience": "1 year",
        "skills": "Python",
        "resume_url": None
    }

    first_response = client.post(
        "/api/v1/candidates/profile", json=payload, headers=headers
    )
    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/candidates/profile", json=payload, headers=headers
    )

    assert second_response.status_code == 409


def test_get_candidate_profile(client):
    candidate_token = create_candidate_token(client)
    headers = {"Authorization": f"Bearer {candidate_token}"}

    # Create profile first
    client.post(
        "/api/v1/candidates/profile",
        json={
            "address": "Indore",
            "education": "MCA",
            "experience": "1 year",
            "skills": "Python, FastAPI",
            "resume_url": None
        },
        headers=headers
    )

    response = client.get("/api/v1/candidates/profile", headers=headers)

    assert response.status_code == 200
    assert response.json()["address"] == "Indore"
    assert response.json()["education"] == "MCA"


def test_get_candidate_profile_not_found(client):
    candidate_token = create_candidate_token(client)

    response = client.get(
        "/api/v1/candidates/profile",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User Profile Not Found"


def test_update_candidate_full_profile(client):
    candidate_token = create_candidate_token(client)
    headers = {"Authorization": f"Bearer {candidate_token}"}

    client.post(
        "/api/v1/candidates/profile",
        json={
            "address": "Indore",
            "education": "BCA",
            "experience": "Fresher",
            "skills": "Python",
            "resume_url": None
        },
        headers=headers
    )

    response = client.put(
        "/api/v1/candidates/profile",
        json={
            "address": "Pune",
            "education": "MCA",
            "experience": "1 year",
            "skills": "Python, FastAPI, SQL",
            "resume_url": "https://example.com/resume.pdf"
        },
        headers=headers
    )

    assert response.status_code == 200
    assert response.json()["address"] == "Pune"
    assert response.json()["education"] == "MCA"
    assert response.json()["experience"] == "1 year"


def test_update_candidate_full_profile_not_found(client):
    candidate_token = create_candidate_token(client)

    response = client.put(
        "/api/v1/candidates/profile",
        json={
            "address": "Pune",
            "education": "MCA",
            "experience": "1 year",
            "skills": "Python",
            "resume_url": None
        },
        headers={"Authorization": f"Bearer {candidate_token}"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User Profile Not Found"


def test_update_candidate_partial_profile(client):
    candidate_token = create_candidate_token(client)
    headers = {"Authorization": f"Bearer {candidate_token}"}

    client.post(
        "/api/v1/candidates/profile",
        json={
            "address": "Indore",
            "education": "BCA",
            "experience": "Fresher",
            "skills": "Python",
            "resume_url": None
        },
        headers=headers
    )

    response = client.patch(
        "/api/v1/candidates/profile",
        json={"skills": "Python, FastAPI, PostgreSQL"},
        headers=headers
    )

    assert response.status_code == 200
    assert response.json()["skills"] == "Python, FastAPI, PostgreSQL"
    assert response.json()["address"] == "Indore"
    assert response.json()["education"] == "BCA"


def test_update_candidate_partial_profile_not_found(client):
    candidate_token = create_candidate_token(client)

    response = client.patch(
        "/api/v1/candidates/profile",
        json={"skills": "Python"},
        headers={"Authorization": f"Bearer {candidate_token}"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User Profile Not Found"


def test_update_candidate_profile_empty_patch(client):
    candidate_token = create_candidate_token(client)

    # Create profile first
    client.post(
        "/api/v1/candidates/profile",
        json={
            "address": "Indore",
            "education": "MCA",
            "experience": "1 year",
            "skills": "Python",
            "resume_url": None
        },
        headers={"Authorization": f"Bearer {candidate_token}"}
    )

    response = client.patch(
        "/api/v1/candidates/profile",
        json={},
        headers={"Authorization": f"Bearer {candidate_token}"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "No Data Provided to Update"


def test_get_candidate_profile_unauthorized(client):
    response = client.get("/api/v1/candidates/profile")
    assert response.status_code == 401


def test_create_candidate_profile_unauthorized(client):
    response = client.post(
        "/api/v1/candidates/profile",
        json={
            "address": "Indore",
            "education": "MCA",
            "experience": "1 year",
            "skills": "Python",
            "resume_url": None
        }
    )

    assert response.status_code == 401


def create_admin_token(client, db_session):
    admin = User(
        full_name="Test Admin",
        email="candidate_profile_admin@example.com",
        hashed_password=hash_password("adminpass123"),
        role="admin",
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "candidate_profile_admin@example.com",
            "password": "adminpass123"
        }
    )

    assert response.status_code == 200
    return response.json()["access_token"]


def test_admin_cannot_create_candidate_profile(client, db_session):
    admin_token = create_admin_token(client, db_session)

    response = client.post(
        "/api/v1/candidates/profile",
        json={"address": "Indore", "education": "MCA"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 403


def test_admin_cannot_view_candidate_profile(client, db_session):
    admin_token = create_admin_token(client, db_session)

    response = client.get(
        "/api/v1/candidates/profile",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 403


def test_admin_cannot_update_candidate_profile(client, db_session):
    admin_token = create_admin_token(client, db_session)

    response = client.put(
        "/api/v1/candidates/profile",
        json={
            "address": "Indore",
            "education": "MCA",
            "experience": "1 year",
            "skills": "Python",
            "resume_url": None
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 403


def test_admin_cannot_patch_candidate_profile(client, db_session):
    admin_token = create_admin_token(client, db_session)

    response = client.patch(
        "/api/v1/candidates/profile",
        json={"skills": "Python"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 403


def test_candidate_cannot_access_another_candidate_profile(client):
    candidate_a_token = create_candidate_token(
        client, "candidate_a@example.com"
    )
    candidate_b_token = create_candidate_token(
        client, "candidate_b@example.com"
    )

    headers_a = {"Authorization": f"Bearer {candidate_a_token}"}
    headers_b = {"Authorization": f"Bearer {candidate_b_token}"}

    create_response = client.post(
        "/api/v1/candidates/profile",
        json={
            "address": "Indore",
            "education": "MCA",
            "experience": "1 year",
            "skills": "Python",
            "resume_url": None
        },
        headers=headers_a
    )
    # print("Candidate A:", candidate_a_token)
    # print("Create response:", create_response.status_code)
    # print("Response body:", create_response.json())
    assert create_response.status_code == 201

    # Candidate B can only see their own profile, which does not exist.
    response = client.get(
        "/api/v1/candidates/profile",
        headers=headers_b
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User Profile Not Found"
