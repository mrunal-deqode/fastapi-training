
from fastapi import APIRouter, HTTPException, Header, Response, status

from models.schemas import JobCreate, JobResponse

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)

jobs = [
    {
        "id": 1,
        "title": "Backend Developer",
        "description": "Build and maintain REST APIs",
        "job_type": "Full-time",
        "deadline": "2026-12-31",
        "location": "Indore",
        "min_experience_years": 1,
        "max_experience_years": 3,
        "salary_min": 300000,
        "salary_max": 600000,
        "status": "open",
        "is_active": True,
    },
    {
        "id": 2,
        "title": "QA Engineer",
        "description": "Test and verify product releases",
        "job_type": "Part-time",
        "deadline": "2026-11-30",
        "location": "Pune",
        "min_experience_years": 0,
        "max_experience_years": 2,
        "salary_min": 200000,
        "salary_max": 400000,
        "status": "open",
        "is_active": True,
    },
]


@router.get("", response_model=list[JobResponse])
def list_jobs(job_type: str | None = None):
    if job_type:
        return [
            job for job in jobs
            if job["job_type"].lower() == job_type.lower()
        ]

    return jobs


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int):
    for job in jobs:
        if job["id"] == job_id:
            return job

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Job not found",
    )


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_job(job: JobCreate):
    new_job = {
        "id": max((item["id"] for item in jobs), default=0) + 1,
        **job.model_dump(),
        "status": "open",
        "is_active": True,
    }

    jobs.append(new_job)
    return new_job


@router.get("/{job_id}/info")
def job_info(
    job_id: int,
    response: Response,
    user_agent: str | None = Header(default=None),
):
    response.headers["X-Job-Id"] = str(job_id)
    response.set_cookie(
        key="last_viewed_job",
        value=str(job_id),
    )

    return {
        "job_id": job_id,
        "your_user_agent": user_agent,
    }
