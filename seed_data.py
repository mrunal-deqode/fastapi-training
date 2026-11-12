
from datetime import date, timedelta

from database import SessionLocal
from models.orm import User, CandidateProfile, Job, Application


db = SessionLocal()

TEMP_PASSWORD = "TEMP_HASH_FOR_DEVELOPMENT_ONLY"

try:
    # --------------------------------
    # 1. Create or retrieve recruiter
    # --------------------------------

    recruiter = db.query(User).filter(
        User.email == "recruiter@test.com"
    ).first()

    if not recruiter:
        recruiter = User(
            email="recruiter@test.com",
            hashed_password=TEMP_PASSWORD,
            role="admin",
            full_name="Rahul Sharma",
            phone="9876543211",
            is_active=True,
        )
        db.add(recruiter)
        db.flush()

    # --------------------------------
    # 2. Create or retrieve candidates
    # --------------------------------

    candidates_data = [
        {
            "email": "candidate@test.com",
            "name": "Asha Verma",
            "phone": "9876543210",
            "address": "Vijay Nagar, Indore",
            "education": "MCA",
            "experience": "1 year as Python Developer",
            "skills": "Python, FastAPI, PostgreSQL, REST API",
        },
        {
            "email": "rohan@test.com",
            "name": "Rohan Patel",
            "phone": "9876543212",
            "address": "Bhopal, Madhya Pradesh",
            "education": "B.Tech Computer Science",
            "experience": "2 years as Java Developer",
            "skills": "Java, Spring Boot, Hibernate, MySQL",
        },
        {
            "email": "priya@test.com",
            "name": "Priya Singh",
            "phone": "9876543213",
            "address": "Pune, Maharashtra",
            "education": "BCA",
            "experience": "Fresher",
            "skills": "React, JavaScript, HTML, CSS",
        },
        {
            "email": "amit@test.com",
            "name": "Amit Gupta",
            "phone": "9876543214",
            "address": "Mumbai, Maharashtra",
            "education": "MCA",
            "experience": "3 years as Backend Developer",
            "skills": "Python, Django, PostgreSQL, Docker",
        },
        {
            "email": "neha@test.com",
            "name": "Neha Joshi",
            "phone": "9876543215",
            "address": "Indore, Madhya Pradesh",
            "education": "B.Tech Information Technology",
            "experience": "1 year as Software Developer",
            "skills": "Java, MySQL, Spring Boot, REST API",
        },
    ]

    candidates = {}

    for data in candidates_data:
        candidate = db.query(User).filter(
            User.email == data["email"]
        ).first()

        if not candidate:
            candidate = User(
                email=data["email"],
                hashed_password=TEMP_PASSWORD,
                role="candidate",
                full_name=data["name"],
                phone=data["phone"],
                is_active=True,
            )
            db.add(candidate)
            db.flush()

        candidates[data["email"]] = candidate

        # Create candidate profile if missing
        profile = db.query(CandidateProfile).filter(
            CandidateProfile.user_id == candidate.id
        ).first()

        if not profile:
            profile = CandidateProfile(
                user_id=candidate.id,
                address=data["address"],
                education=data["education"],
                experience=data["experience"],
                skills=data["skills"],
                resume_url=None,
            )
            db.add(profile)

    db.flush()

    # --------------------------------
    # 3. Create or retrieve jobs
    # --------------------------------

    jobs_data = [
        {
            "title": "Backend Developer",
            "description": "Build and maintain REST APIs using Python and FastAPI.",
            "job_type": "Full-time",
            "location": "Indore",
            "min_exp": 0,
            "max_exp": 3,
            "salary_min": 300000,
            "salary_max": 600000,
            "status": "open",
        },
        {
            "title": "Java Developer",
            "description": "Develop enterprise applications using Java and Spring Boot.",
            "job_type": "Full-time",
            "location": "Pune",
            "min_exp": 1,
            "max_exp": 4,
            "salary_min": 400000,
            "salary_max": 800000,
            "status": "open",
        },
        {
            "title": "React Developer",
            "description": "Build responsive frontend applications using React and JavaScript.",
            "job_type": "Full-time",
            "location": "Mumbai",
            "min_exp": 0,
            "max_exp": 3,
            "salary_min": 300000,
            "salary_max": 700000,
            "status": "open",
        },
        {
            "title": "Data Analyst",
            "description": "Analyze business data and prepare reports using SQL and Python.",
            "job_type": "Full-time",
            "location": "Bangalore",
            "min_exp": 1,
            "max_exp": 3,
            "salary_min": 350000,
            "salary_max": 650000,
            "status": "open",
        },
        {
            "title": "QA Engineer",
            "description": "Perform manual and automation testing of web applications.",
            "job_type": "Contract",
            "location": "Indore",
            "min_exp": 1,
            "max_exp": 4,
            "salary_min": 300000,
            "salary_max": 550000,
            "status": "closed",
        },
    ]

    jobs = {}

    for data in jobs_data:
        job = db.query(Job).filter(
            Job.title == data["title"],
            Job.created_by == recruiter.id,
        ).first()

        if not job:
            job = Job(
                title=data["title"],
                description=data["description"],
                job_type=data["job_type"],
                deadline=date.today() + timedelta(days=30),
                location=data["location"],
                min_experience_years=data["min_exp"],
                max_experience_years=data["max_exp"],
                salary_min=data["salary_min"],
                salary_max=data["salary_max"],
                status=data["status"],
                is_active=True,
                created_by=recruiter.id,
            )
            db.add(job)
            db.flush()

        jobs[data["title"]] = job

    # --------------------------------
    # 4. Create applications
    # --------------------------------

    applications_data = [
        ("candidate@test.com", "Backend Developer", 1, "Applied"),
        ("candidate@test.com", "React Developer", 1, "Under Review"),
        ("rohan@test.com", "Java Developer", 2, "Shortlisted"),
        ("rohan@test.com", "Backend Developer", 2, "Under Review"),
        ("priya@test.com", "React Developer", 0, "Applied"),
        ("priya@test.com", "Data Analyst", 0, "Applied"),
        ("amit@test.com", "Backend Developer", 3, "Selected"),
        ("amit@test.com", "Data Analyst", 3, "Rejected"),
        ("neha@test.com", "Java Developer", 1, "Applied"),
        ("neha@test.com", "Backend Developer", 1, "Shortlisted"),
    ]

    for email, job_title, experience, app_status in applications_data:
        candidate = candidates[email]
        job = jobs[job_title]

        existing_application = db.query(Application).filter(
            Application.candidate_id == candidate.id,
            Application.job_id == job.id,
        ).first()

        if not existing_application:
            application = Application(
                candidate_id=candidate.id,
                job_id=job.id,
                years_of_experience=experience,
                cover_letter=f"I am interested in the {job_title} position.",
                status=app_status,
                is_active=True,
            )
            db.add(application)

    # --------------------------------
    # 5. Commit all records
    # --------------------------------

    db.commit()

    # print("\nDevelopment seed completed successfully!")
    # print("Recruiter ID:", recruiter.id)

    # print("\nCandidates:")
    # for email, candidate in candidates.items():
    # print(email, "-> ID:", candidate.id)

    # print("\nJobs:")
    # for title, job in jobs.items():
    # print(title, "-> ID:", job.id)

    # print("\nTotal candidates:", len(candidates))
    # print("Total jobs:", len(jobs))
    # print("Application seed entries:", len(applications_data))

except Exception:
    db.rollback()
    raise

finally:
    db.close()
