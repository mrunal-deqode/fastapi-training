from sqlalchemy import event

from models.orm import Application, Job, User
from utils.jwt import create_access_token
from utils.security import hash_password


def create_admin_token(client, db_session, email="admin_test@example.com"):
    admin = User(
        full_name="Test Admin",
        email=email,
        hashed_password=hash_password("adminpass123"),
        role="admin",
        is_active=True
    )

    db_session.add(admin)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "adminpass123"
        }
    )

    assert response.status_code == 200
    return response.json()["access_token"]


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


def create_test_job(client, admin_token):
    response = client.post(
        "/api/v1/jobs",
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
        "/api/v1/applications",
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
        "/api/v1/applications",
        json=payload,
        headers=headers
    )

    second_response = client.post(
        "/api/v1/applications",
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
        "/api/v1/applications",
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
        "/api/v1/applications",
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
        "/api/v1/applications",
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

    response = client.get("/api/v1/jobs")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["title"] == "Python Developer"


def test_get_job_details(client, db_session):
    admin_token = create_admin_token(client, db_session)
    job_id = create_test_job(client, admin_token)

    response = client.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json()["id"] == job_id
    assert response.json()["title"] == "Python Developer"


def test_get_closed_job_not_found(client, db_session):
    admin_token = create_admin_token(client, db_session)
    job_id = create_test_job(client, admin_token)

    job = db_session.query(Job).filter(Job.id == job_id).first()
    job.status = "closed"
    db_session.commit()

    response = client.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_candidate_get_my_applications(client, db_session):
    admin_token = create_admin_token(client, db_session)
    candidate_token = create_candidate_token(client)
    job_id = create_test_job(client, admin_token)

    client.post(
        "/api/v1/applications",
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
        "/api/v1/applications/my-applications",
        headers={
            "Authorization": f"Bearer {candidate_token}"
        }
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["job_id"] == job_id


def test_candidate_get_my_applications_unauthorized(client):
    response = client.get("/api/v1/applications/my-applications")

    assert response.status_code == 401


def test_candidate_cannot_access_another_candidates_application(
    client, db_session
):
    admin_token = create_admin_token(client, db_session)

    candidate_a_token = create_candidate_token(
        client, "candidate_a@example.com"
    )
    candidate_b_token = create_candidate_token(
        client, "candidate_b@example.com"
    )

    job_id = create_test_job(client, admin_token)

    application_response = client.post(
        "/api/v1/applications",
        json={
            "job_id": job_id,
            "years_of_experience": 2,
            "cover_letter": "Candidate A application."
        },
        headers={
            "Authorization": f"Bearer {candidate_a_token}"
        }
    )

    assert application_response.status_code == 201
    application_id = application_response.json()["id"]

    response = client.get(
        f"/api/v1/applications/{application_id}",
        headers={
            "Authorization": f"Bearer {candidate_b_token}"
        }
    )

    assert response.status_code == 403
    assert response.json()[
        "detail"] == "You do not have permission to access this application"


def test_candidate_cannot_replace_another_candidates_application(
    client, db_session
):
    admin_token = create_admin_token(client, db_session)
    candidate_a = create_candidate_token(client, "replace_a@example.com")
    candidate_b = create_candidate_token(client, "replace_b@example.com")
    job_id = create_test_job(client, admin_token)

    application = client.post(
        "/api/v1/applications",
        json={
            "job_id": job_id,
            "years_of_experience": 2,
            "cover_letter": "Candidate A application."
        },
        headers={"Authorization": f"Bearer {candidate_a}"}
    )
    application_id = application.json()["id"]

    response = client.put(
        f"/api/v1/applications/{application_id}",
        json={
            "years_of_experience": 5,
            "cover_letter": "Unauthorized update."
        },
        headers={"Authorization": f"Bearer {candidate_b}"}
    )

    assert response.status_code == 403


def test_candidate_cannot_patch_another_candidates_application(
    client, db_session
):
    admin_token = create_admin_token(client, db_session)
    candidate_a = create_candidate_token(client, "patch_a@example.com")
    candidate_b = create_candidate_token(client, "patch_b@example.com")
    job_id = create_test_job(client, admin_token)

    application = client.post(
        "/api/v1/applications",
        json={
            "job_id": job_id,
            "years_of_experience": 2,
            "cover_letter": "Candidate A application."
        },
        headers={"Authorization": f"Bearer {candidate_a}"}
    )
    application_id = application.json()["id"]

    response = client.patch(
        f"/api/v1/applications/{application_id}",
        json={"years_of_experience": 5},
        headers={"Authorization": f"Bearer {candidate_b}"}
    )

    assert response.status_code == 403


def test_candidate_cannot_delete_another_candidates_application(
    client, db_session
):
    admin_token = create_admin_token(client, db_session)
    candidate_a = create_candidate_token(client, "delete_a@example.com")
    candidate_b = create_candidate_token(client, "delete_b@example.com")
    job_id = create_test_job(client, admin_token)

    application = client.post(
        "/api/v1/applications",
        json={
            "job_id": job_id,
            "years_of_experience": 2,
            "cover_letter": "Candidate A application."
        },
        headers={"Authorization": f"Bearer {candidate_a}"}
    )
    application_id = application.json()["id"]

    response = client.delete(
        f"/api/v1/applications/{application_id}",
        headers={"Authorization": f"Bearer {candidate_b}"}
    )

    assert response.status_code == 403


def test_candidate_cannot_assign_application_to_another_candidate(
    client, db_session
):
    admin_token = create_admin_token(client, db_session)
    candidate_a = create_candidate_token(client, "mass_a@example.com")
    job_id = create_test_job(client, admin_token)

    response = client.post(
        "/api/v1/applications",
        json={
            "job_id": job_id,
            "candidate_id": 999999,
            "years_of_experience": 2,
            "cover_letter": "Testing mass assignment."
        },
        headers={"Authorization": f"Bearer {candidate_a}"}
    )

    assert response.status_code == 422


def test_admin_cannot_access_another_admins_application(
    client, db_session
):
    admin_a = create_admin_token(
        client, db_session, "admin_a@example.com"
    )
    admin_b = create_admin_token(
        client, db_session, "admin_b@example.com"
    )

    candidate_token = create_candidate_token(
        client, "admin_bola_candidate@example.com"
    )

    job_id = create_test_job(client, admin_a)

    application = client.post(
        "/api/v1/applications",
        json={
            "job_id": job_id,
            "years_of_experience": 2,
            "cover_letter": "Test application."
        },
        headers={"Authorization": f"Bearer {candidate_token}"}
    )

    assert application.status_code == 201
    application_id = application.json()["id"]

    response = client.get(
        f"/api/v1/applications/{application_id}",
        headers={"Authorization": f"Bearer {admin_b}"}
    )

    assert response.status_code == 403


def test_admin_cannot_update_another_admins_application_status(
    client, db_session
):
    admin_a = create_admin_token(
        client, db_session, "status_admin_a@example.com"
    )
    admin_b = create_admin_token(
        client, db_session, "status_admin_b@example.com"
    )

    candidate_token = create_candidate_token(
        client, "status_candidate@example.com"
    )

    job_id = create_test_job(client, admin_a)

    application = client.post(
        "/api/v1/applications",
        json={
            "job_id": job_id,
            "years_of_experience": 2,
            "cover_letter": "Test application."
        },
        headers={"Authorization": f"Bearer {candidate_token}"}
    )

    application_id = application.json()["id"]

    response = client.patch(
        f"/api/v1/applications/admin/applications/{application_id}/status",
        json={"status": "Shortlisted"},
        headers={"Authorization": f"Bearer {admin_b}"}
    )

    assert response.status_code == 403
    updated_application = db_session.query(Application).filter(
        Application.id == application_id
    ).first()

    assert updated_application.status == "Applied"


def test_admin_applicant_list_uses_efficient_queries(client, db_session):
    admin_token = create_admin_token(
        client, db_session, "perf_admin@example.com"
    )
    job_id = create_test_job(client, admin_token)

    for index in range(5):
        candidate_token = create_candidate_token(
            client, f"perf_candidate_{index}@example.com"
        )

        response = client.post(
            "/api/v1/applications",
            json={
                "job_id": job_id,
                "years_of_experience": 2,
                "cover_letter": "Performance test application."
            },
            headers={
                "Authorization": f"Bearer {candidate_token}"
            }
        )
        assert response.status_code == 201

    db_session.expunge_all()

    queries = []

    def count_queries(
        conn, cursor, statement, parameters, context, executemany
    ):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)

    connection = db_session.connection()
    event.listen(connection, "before_cursor_execute", count_queries)

    try:
        response = client.get(
            f"/api/v1/applications/admin/jobs/{job_id}/appliactions",
            headers={
                "Authorization": f"Bearer {admin_token}"
            }
        )
    finally:
        event.remove(connection, "before_cursor_execute", count_queries)

    assert response.status_code == 200
    assert len(response.json()["items"]) == 5
    assert len(queries) == 6


def test_candidate_cannot_access_admin_applicant_list(client, db_session):
    admin_token = create_admin_token(client, db_session)
    candidate_token = create_candidate_token(client)
    job_id = create_test_job(client, admin_token)

    response = client.get(
        f"/api/v1/applications/admin/jobs/{job_id}/appliactions",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )

    assert response.status_code == 403


def test_candidate_cannot_access_admin_applicant_details(client, db_session):
    admin_token = create_admin_token(client, db_session)
    candidate_token = create_candidate_token(client)
    job_id = create_test_job(client, admin_token)

    application = client.post(
        "/api/v1/applications",
        json={
            "job_id": job_id,
            "years_of_experience": 2,
            "cover_letter": "Test application.",
        },
        headers={"Authorization": f"Bearer {candidate_token}"},
    )

    assert application.status_code == 201
    application_id = application.json()["id"]

    response = client.get(
        f"/api/v1/applications/admin/applications/{application_id}",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )

    assert response.status_code == 403


def test_candidate_cannot_update_application_status(client, db_session):
    admin_token = create_admin_token(client, db_session)
    candidate_token = create_candidate_token(client)
    job_id = create_test_job(client, admin_token)

    application = client.post(
        "/api/v1/applications",
        json={
            "job_id": job_id,
            "years_of_experience": 2,
            "cover_letter": "Test application.",
        },
        headers={"Authorization": f"Bearer {candidate_token}"},
    )

    assert application.status_code == 201
    application_id = application.json()["id"]

    response = client.patch(
        f"/api/v1/applications/admin/applications/{application_id}/status",
        json={"status": "Shortlisted"},
        headers={"Authorization": f"Bearer {candidate_token}"},
    )

    assert response.status_code == 403


def test_super_admin_can_access_any_candidates_application(client, db_session):
    admin_token = create_admin_token(client, db_session)
    candidate_token = create_candidate_token(client)
    job_id = create_test_job(client, admin_token)

    application = client.post(
        "/api/v1/applications",
        json={
            "job_id": job_id,
            "years_of_experience": 2,
            "cover_letter": "Test application.",
        },
        headers={"Authorization": f"Bearer {candidate_token}"},
    )

    assert application.status_code == 201
    application_id = application.json()["id"]

    super_admin = User(
        full_name="Test Super Admin",
        email="super_admin_test@example.com",
        hashed_password=hash_password("password123"),
        role="super_admin",
        is_active=True,
    )

    db_session.add(super_admin)
    db_session.commit()
    db_session.refresh(super_admin)

    super_admin_token = create_access_token({
        "sub": str(super_admin.id),
        "role": super_admin.role,
    })

    response = client.get(
        f"/api/v1/applications/{application_id}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == application_id


def test_admin_cannot_view_another_admins_applicant_details(
    client, db_session
):
    admin_a = create_admin_token(
        client, db_session, "detail_admin_a@example.com"
    )
    admin_b = create_admin_token(
        client, db_session, "detail_admin_b@example.com"
    )
    candidate_token = create_candidate_token(
        client, "detail_candidate@example.com"
    )

    job_id = create_test_job(client, admin_a)

    application = client.post(
        "/api/v1/applications",
        json={
            "job_id": job_id,
            "years_of_experience": 2,
            "cover_letter": "Test application.",
        },
        headers={"Authorization": f"Bearer {candidate_token}"},
    )

    assert application.status_code == 201

    application_id = application.json()["id"]

    response = client.get(
        f"/api/v1/applications/admin/applications/{application_id}",
        headers={"Authorization": f"Bearer {admin_b}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have permission to view this application"
    )


def test_admin_cannot_list_another_admins_applicants(client, db_session):
    admin_a = create_admin_token(
        client, db_session, "list_admin_a@example.com"
    )
    admin_b = create_admin_token(
        client, db_session, "list_admin_b@example.com"
    )

    job_id = create_test_job(client, admin_a)

    response = client.get(
        f"/api/v1/applications/admin/jobs/{job_id}/appliactions",
        headers={"Authorization": f"Bearer {admin_b}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have permission to view applicants for this job"
    )


def test_admin_can_only_list_own_jobs(client, db_session):
    admin_a = create_admin_token(
        client, db_session, "jobs_admin_a@example.com"
    )
    admin_b = create_admin_token(
        client, db_session, "jobs_admin_b@example.com"
    )

    job_a = create_test_job(client, admin_a)
    create_test_job(client, admin_b)

    response = client.get(
        "/api/v1/jobs/manage",
        headers={"Authorization": f"Bearer {admin_a}"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == job_a


def test_candidate_cannot_access_admin_job_management(client):
    candidate_token = create_candidate_token(client)

    response = client.get(
        "/api/v1/jobs/manage",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )

    assert response.status_code == 403


def test_candidate_cannot_create_job(client):
    candidate_token = create_candidate_token(client)

    response = client.post(
        "/api/v1/jobs",
        json={
            "title": "Python Developer",
            "description": "Looking for a Python developer.",
            "job_type": "Full-time",
            "deadline": "2027-12-31",
            "location": "Indore",
            "min_experience_years": 0,
        },
        headers={"Authorization": f"Bearer {candidate_token}"},
    )

    assert response.status_code == 403


def test_candidate_filter_applications_by_status(client, db_session):
    admin_token = create_admin_token(client, db_session)
    candidate_token = create_candidate_token(client)
    job_id = create_test_job(client, admin_token)

    application = client.post(
        "/api/v1/applications",
        json={
            "job_id": job_id,
            "years_of_experience": 2,
            "cover_letter": "Test application."
        },
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert application.status_code == 201

    db_application = db_session.query(Application).filter(
        Application.id == application.json()["id"]
    ).first()
    db_application.status = "Shortlisted"
    db_session.commit()

    response = client.get(
        "/api/v1/applications/my-applications?status=Shortlisted",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["status"] == "Shortlisted"


def test_candidate_filter_applications_by_job_id(client, db_session):
    admin_token = create_admin_token(client, db_session)
    candidate_token = create_candidate_token(client)

    job_id_1 = create_test_job(client, admin_token)
    job_id_2 = create_test_job(client, admin_token)

    for job_id in [job_id_1, job_id_2]:
        response = client.post(
            "/api/v1/applications",
            json={
                "job_id": job_id,
                "years_of_experience": 2,
                "cover_letter": "Test application."
            },
            headers={"Authorization": f"Bearer {candidate_token}"}
        )
        assert response.status_code == 201

    response = client.get(
        f"/api/v1/applications/my-applications?job_id={job_id_1}",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["job_id"] == job_id_1


def test_candidate_filter_with_pagination(client, db_session):
    admin_token = create_admin_token(client, db_session)
    candidate_token = create_candidate_token(client)

    job_ids = [
        create_test_job(client, admin_token)
        for _ in range(3)
    ]

    for job_id in job_ids:
        response = client.post(
            "/api/v1/applications",
            json={
                "job_id": job_id,
                "years_of_experience": 2,
                "cover_letter": "Test application."
            },
            headers={"Authorization": f"Bearer {candidate_token}"}
        )
        assert response.status_code == 201

    applications = db_session.query(Application).filter(
        Application.candidate_id == db_session.query(User.id).filter(
            User.email == "applicant_test@example.com"
        ).scalar_subquery()
    ).all()

    applications[1].status = "Shortlisted"
    db_session.commit()

    response = client.get(
        "/api/v1/applications/my-applications"
        "?status=Applied&page=1&limit=1",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["status"] == "Applied"


def test_candidate_filters_cannot_expose_another_candidates_applications(
    client, db_session
):
    admin_token = create_admin_token(client, db_session)
    candidate_a = create_candidate_token(client, "filter_a@example.com")
    candidate_b = create_candidate_token(client, "filter_b@example.com")
    job_id = create_test_job(client, admin_token)

    for token in [candidate_a, candidate_b]:
        response = client.post(
            "/api/v1/applications",
            json={
                "job_id": job_id,
                "years_of_experience": 2,
                "cover_letter": "Test application."
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201

    response = client.get(
        "/api/v1/applications/my-applications?status=Applied",
        headers={"Authorization": f"Bearer {candidate_a}"}
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["candidate_id"] != (
        db_session.query(User.id)
        .filter(User.email == "filter_b@example.com")
        .scalar()
    )


def test_admin_filter_applicants_by_status(client, db_session):
    admin_token = create_admin_token(client, db_session)
    job_id = create_test_job(client, admin_token)

    for index in range(2):
        candidate_token = create_candidate_token(
            client, f"admin_filter_{index}@example.com"
        )
        response = client.post(
            "/api/v1/applications",
            json={
                "job_id": job_id,
                "years_of_experience": 2,
                "cover_letter": "Admin filter test."
            },
            headers={"Authorization": f"Bearer {candidate_token}"}
        )
        assert response.status_code == 201

        if index == 1:
            application = db_session.query(Application).filter(
                Application.id == response.json()["id"]
            ).first()
            application.status = "Shortlisted"
            db_session.commit()

    response = client.get(
        f"/api/v1/applications/admin/jobs/{job_id}/appliactions"
        "?status=Shortlisted",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["status"] == "Shortlisted"


def test_admin_filter_applicants_with_pagination(client, db_session):
    admin_token = create_admin_token(client, db_session)
    job_id = create_test_job(client, admin_token)

    for index in range(3):
        candidate_token = create_candidate_token(
            client, f"admin_page_filter_{index}@example.com"
        )
        response = client.post(
            "/api/v1/applications",
            json={
                "job_id": job_id,
                "years_of_experience": 2,
                "cover_letter": "Admin pagination test."
            },
            headers={"Authorization": f"Bearer {candidate_token}"}
        )
        assert response.status_code == 201

        if index == 2:
            application = db_session.query(Application).filter(
                Application.id == response.json()["id"]
            ).first()
            application.status = "Rejected"
            db_session.commit()

    response = client.get(
        f"/api/v1/applications/admin/jobs/{job_id}/appliactions"
        "?status=Applied&page=1&limit=1",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["status"] == "Applied"


def test_updating_application_status_invalidates_both_dashboards(
    client, db_session, monkeypatch
):
    import routers.applications as applications_router

    invalidated_users = []

    def fake_clear_dashboard_cache(user_id):
        invalidated_users.append(user_id)

    monkeypatch.setattr(
        applications_router,
        "clear_dashboard_cache",
        fake_clear_dashboard_cache,
    )

    admin_token = create_admin_token(
        client, db_session, "cache_admin@example.com"
    )
    candidate_token = create_candidate_token(
        client, "cache_candidate@example.com"
    )
    job_id = create_test_job(client, admin_token)

    application_response = client.post(
        "/api/v1/applications",
        json={
            "job_id": job_id,
            "years_of_experience": 2,
            "cover_letter": "Testing dashboard invalidation.",
        },
        headers={"Authorization": f"Bearer {candidate_token}"},
    )

    assert application_response.status_code == 201
    application_id = application_response.json()["id"]

    # Ignore invalidations caused by creating the application.
    invalidated_users.clear()

    response = client.patch(
        f"/api/v1/applications/admin/applications/{application_id}/status",
        json={"status": "Shortlisted"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200

    candidate = db_session.query(User).filter_by(
        email="cache_candidate@example.com"
    ).first()
    admin = db_session.query(User).filter_by(
        email="cache_admin@example.com"
    ).first()

    assert set(invalidated_users) == {candidate.id, admin.id}
