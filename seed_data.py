
from datetime import date, timedelta

from database import SessionLocal
from models.orm import User, Job


db = SessionLocal()

try:
    candidate = User(
        email="candidate@test.com",
        hashed_password="TEMP_HASH_FOR_DEVELOPMENT_ONLY",
        role="candidate",
        full_name="Asha Verma",
        phone="9876543210",
        is_active=True,
    )

    recruiter = User(
        email="recruiter@test.com",
        hashed_password="TEMP_HASH_FOR_DEVELOPMENT_ONLY",
        role="admin",
        full_name="Rahul Sharma",
        phone="9876543211",
        is_active=True,
    )

    db.add_all([candidate, recruiter])
    db.flush()

    job = Job(
        title="Backend Developer",
        description="Build and maintain REST APIs using Python and FastAPI.",
        job_type="Full-time",
        deadline=date.today() + timedelta(days=30),
        location="Indore",
        min_experience_years=0,
        max_experience_years=3,
        salary_min=300000,
        salary_max=600000,
        status="open",
        is_active=True,
        created_by=recruiter.id,
    )

    db.add(job)
    db.commit()

    print("Development test records created successfully.")
    print("Candidate ID:", candidate.id)
    print("Recruiter ID:", recruiter.id)
    print("Job ID:", job.id)

except Exception:
    db.rollback()
    raise

finally:
    db.close()
