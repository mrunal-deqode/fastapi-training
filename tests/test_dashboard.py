from datetime import date

from models.orm import Application, Job, User
from utils.jwt import create_access_token
from utils.security import hash_password


class FakeRedis:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def setex(self, key, ttl, value):
        self.data[key] = value

    def scan_iter(self, match=None):
        prefix = match.removesuffix("*")
        for key in list(self.data):
            if key.startswith(prefix):
                yield key

    def delete(self, *keys):
        for key in keys:
            self.data.pop(key, None)


def test_candidate_dashboard_is_user_scoped_and_cached(
    client, db_session, monkeypatch
):
    import routers.dashboard as dashboard

    fake_redis = FakeRedis()
    monkeypatch.setattr(dashboard, "redis_client", fake_redis)

    candidate = User(
        full_name="Candidate One",
        email="dashboard_candidate1@example.com",
        hashed_password=hash_password("password123"),
        role="candidate",
        is_active=True,
    )
    another_candidate = User(
        full_name="Candidate Two",
        email="dashboard_candidate2@example.com",
        hashed_password=hash_password("password123"),
        role="candidate",
        is_active=True,
    )
    admin = User(
        full_name="Dashboard Admin",
        email="dashboard_admin@example.com",
        hashed_password=hash_password("password123"),
        role="admin",
        is_active=True,
    )

    db_session.add_all([candidate, another_candidate, admin])
    db_session.flush()

    job = Job(
        title="Python Developer",
        description="Python backend development role.",
        job_type="Full-time",
        deadline=date(2027, 12, 31),
        created_by=admin.id,
    )
    another_job = Job(
        title="Java Developer",
        description="Java backend development role.",
        job_type="Full-time",
        deadline=date(2027, 12, 31),
        created_by=admin.id,
    )

    db_session.add_all([job, another_job])
    db_session.flush()

    db_session.add_all([
        Application(
            candidate_id=candidate.id,
            job_id=job.id,
            years_of_experience=2,
            status="Applied",
        ),
        Application(
            candidate_id=another_candidate.id,
            job_id=another_job.id,
            years_of_experience=3,
            status="Selected",
        ),
    ])
    db_session.commit()

    token = create_access_token({
        "sub": str(candidate.id),
        "role": "candidate",
    })

    response = client.get(
        "/api/v1/dashboard/candidate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_applications"] == 1
    assert data["status_counts"]["Applied"] == 1
    assert data["status_counts"]["Selected"] == 0
    assert len(data["recent_applications"]) == 1
    assert data["recent_applications"][0]["job_title"] == "Python Developer"

    assert f"dashboard:{candidate.id}:candidate" in fake_redis.data

    second_response = client.get(
        "/api/v1/dashboard/candidate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert second_response.status_code == 200
    assert second_response.json() == data


def test_admin_dashboard_is_user_scoped_and_cached(
    client, db_session, monkeypatch
):
    import routers.dashboard as dashboard

    fake_redis = FakeRedis()
    monkeypatch.setattr(dashboard, "redis_client", fake_redis)

    admin_a = User(
        full_name="Admin A",
        email="dashboard_admin_a@example.com",
        hashed_password=hash_password("password123"),
        role="admin",
        is_active=True,
    )
    admin_b = User(
        full_name="Admin B",
        email="dashboard_admin_b@example.com",
        hashed_password=hash_password("password123"),
        role="admin",
        is_active=True,
    )
    candidate = User(
        full_name="Dashboard Candidate",
        email="dashboard_applicant@example.com",
        hashed_password=hash_password("password123"),
        role="candidate",
        is_active=True,
    )

    db_session.add_all([admin_a, admin_b, candidate])
    db_session.flush()

    job_a = Job(
        title="Python Developer",
        description="Python backend development role.",
        job_type="Full-time",
        deadline=date(2027, 12, 31),
        created_by=admin_a.id,
    )
    job_b = Job(
        title="Java Developer",
        description="Java backend development role.",
        job_type="Full-time",
        deadline=date(2027, 12, 31),
        created_by=admin_b.id,
    )

    db_session.add_all([job_a, job_b])
    db_session.flush()

    db_session.add_all([
        Application(
            candidate_id=candidate.id,
            job_id=job_a.id,
            years_of_experience=2,
            status="Applied",
        ),
        Application(
            candidate_id=candidate.id,
            job_id=job_b.id,
            years_of_experience=3,
            status="Selected",
        ),
    ])
    db_session.commit()

    token_a = create_access_token({
        "sub": str(admin_a.id),
        "role": "admin",
    })

    response = client.get(
        "/api/v1/dashboard/admin",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_jobs"] == 1
    assert data["total_applications"] == 1
    assert data["status_counts"]["Applied"] == 1
    assert data["status_counts"]["Selected"] == 0
    assert len(data["recent_applicants"]) == 1
    assert data["recent_applicants"][0]["job_title"] == "Python Developer"

    assert f"dashboard:{admin_a.id}:admin" in fake_redis.data
    assert f"dashboard:{admin_b.id}:admin" not in fake_redis.data

    second_response = client.get(
        "/api/v1/dashboard/admin",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert second_response.status_code == 200
    assert second_response.json() == data


def test_clear_dashboard_cache_only_removes_target_user_keys(monkeypatch):
    from redis_client import clear_dashboard_cache

    fake_redis = FakeRedis()
    fake_redis.data = {
        "dashboard:1:candidate": "candidate-data",
        "dashboard:1:admin": "admin-data",
        "dashboard:2:candidate": "other-user-data",
    }

    monkeypatch.setattr("redis_client.redis_client", fake_redis)

    clear_dashboard_cache(1)

    assert "dashboard:1:candidate" not in fake_redis.data
    assert "dashboard:1:admin" not in fake_redis.data
    assert fake_redis.data["dashboard:2:candidate"] == "other-user-data"
