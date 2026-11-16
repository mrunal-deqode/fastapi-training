
from models.orm import User
from utils.security import hash_password
from models.orm import User, Job


def create_admin_token(client, db_session):
    admin = User(
        full_name="Test Admin",
        email="admin_test@example.com",
        hashed_password=hash_password("adminpass123"),
        role="admin",
        is_active=True
    )

    db_session.add(admin)
    db_session.commit()

    response = client.post(
        "/auth/login",
        data={
            "username": "admin_test@example.com",
            "password": "adminpass123"
        }
    )

    assert response.status_code == 200
    return response.json()["access_token"]

def create_candidate_token(client):
    payload = {
        "full_name": "Test Applicant",
        "email": "applicant_test@example.com",
        "password": "password123"
    }

    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={
            "username": payload["email"],
            "password": payload["password"]
        }
    )

    assert login_response.status_code == 200
    return login_response.json()["access_token"]

def create_test_job(client, admin_token):
    response = client.post(
        "/jobs",
        json={
            "title": "Python Developer",
            "description": "Looking for a Python developer.",
            "job_type": "Full-time",
            "deadline": "2027-12-31",
            "location": "Indore",
            "min_experience_years": 0
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert response.status_code == 201
    return response.json()["id"]


def test_candidate_apply_success(client, db_session):
    admin_token = create_admin_token(client, db_session)
    candidate_token = create_candidate_token(client)
    job_id = create_test_job(client, admin_token)

    response = client.post(
        "/applications",
        json={
            "job_id": job_id,
            "years_of_experience": 2,
            "cover_letter": "I am interested in this position."
        },
        headers={
            "Authorization": f"Bearer {candidate_token}"
        }
    )

    assert response.status_code == 201
    assert response.json()["job_id"] == job_id
    assert response.json()["years_of_experience"] == 2
    assert response.json()["status"] == "Applied"


def test_duplicate_application_rejected(client, db_session):
    admin_token = create_admin_token(client, db_session)
    candidate_token = create_candidate_token(client)
    job_id = create_test_job(client, admin_token)

    headers = {
        "Authorization": f"Bearer {candidate_token}"
    }

    payload = {
        "job_id": job_id,
        "years_of_experience": 2,
        "cover_letter": "I am interested."
    }

    first_response = client.post(
        "/applications",
        json=payload,
        headers=headers
    )

    second_response = client.post(
        "/applications",
        json=payload,
        headers=headers
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Candidate has already applied for this job"
    )


def test_application_for_nonexistent_job(client):
    candidate_token = create_candidate_token(client)

    response = client.post(
        "/applications",
        json={
            "job_id": 999999,
            "years_of_experience": 1,
            "cover_letter": "Test application."
        },
        headers={
            "Authorization": f"Bearer {candidate_token}"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Active open job not found"


def test_application_to_closed_job_rejected(client, db_session):
    admin_token = create_admin_token(client, db_session)
    candidate_token = create_candidate_token(client)
    job_id = create_test_job(client, admin_token)

    job = db_session.query(Job).filter(Job.id == job_id).first()
    job.status = "closed"
    db_session.commit()

    response = client.post(
        "/applications",
        json={
            "job_id": job_id,
            "years_of_experience": 2,
            "cover_letter": "Interested in this job."
        },
        headers={
            "Authorization": f"Bearer {candidate_token}"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Active open job not found"


def test_application_to_inactive_job_rejected(client, db_session):
    admin_token = create_admin_token(client, db_session)
    candidate_token = create_candidate_token(client)
    job_id = create_test_job(client, admin_token)

    job = db_session.query(Job).filter(Job.id == job_id).first()
    job.is_active = False
    db_session.commit()

    response = client.post(
        "/applications",
        json={
            "job_id": job_id,
            "years_of_experience": 2,
            "cover_letter": "Interested in this job."
        },
        headers={
            "Authorization": f"Bearer {candidate_token}"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Active open job not found"


def test_list_open_jobs(client, db_session):
    admin_token = create_admin_token(client, db_session)
    create_test_job(client, admin_token)

    response = client.get("/jobs")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Python Developer"


def test_get_job_details(client, db_session):
    admin_token = create_admin_token(client, db_session)
    job_id = create_test_job(client, admin_token)

    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json()["id"] == job_id
    assert response.json()["title"] == "Python Developer"


def test_get_closed_job_not_found(client, db_session):
    admin_token = create_admin_token(client, db_session)
    job_id = create_test_job(client, admin_token)

    job = db_session.query(Job).filter(Job.id == job_id).first()
    job.status = "closed"
    db_session.commit()

    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_candidate_get_my_applications(client, db_session):
    admin_token = create_admin_token(client, db_session)
    candidate_token = create_candidate_token(client)
    job_id = create_test_job(client, admin_token)

    client.post(
        "/applications",
        json={
            "job_id": job_id,
            "years_of_experience": 2,
            "cover_letter": "Interested in this position."
        },
        headers={
            "Authorization": f"Bearer {candidate_token}"
        }
    )

    response = client.get(
        "/applications/my-applications",
        headers={
            "Authorization": f"Bearer {candidate_token}"
        }
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["job_id"] == job_id


def test_candidate_get_my_applications_unauthorized(client):
    response = client.get("/applications/my-applications")

    assert response.status_code == 401
