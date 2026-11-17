
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from database import get_db
from models.orm import Job, User
from models.schemas import JobCreate, JobResponse
from redis_client import clear_job_cache, redis_client
from utils.dependencies import require_roles
from utils.module7_dependencies import pagniation

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


@router.get("", response_model=list[JobResponse])
def list_jobs(job_type: str | None = Query(default=None, min_length=2, max_length=30), db: Session = Depends(get_db), pagination_data: dict = Depends(pagniation)):
    skip = pagination_data["skip"]
    limit = pagination_data["limit"]

    cache_key = f"jobs:list:{job_type or 'all'}:{skip}:{limit}"

    cached_jobs = redis_client.get(cache_key)

    if cached_jobs:
        return json.loads(cached_jobs)

    query = db.query(Job).filter(
        Job.is_active.is_(True),
        Job.status == "open"
    )

    if job_type:
        query = query.filter(Job.job_type.ilike(job_type))

    jobs = query.offset(skip).limit(limit).all()

    jobs_data = [JobResponse.model_validate(
        job).model_dump(mode="json") for job in jobs]

    redis_client.setex(cache_key, 60, json.dumps(jobs_data))

    return jobs_data


@router.get("/manage", response_model=list[JobResponse])
def get_all_job_for_admin(current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    jobs = db.query(Job).filter(Job.created_by == current_user.id).all()

    return jobs


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.is_active.is_(True),
        Job.status == "open"
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return job


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(job_data: JobCreate, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    recruiter = db.query(User).filter(
        User.id == current_user.id,
        User.role == "admin",
        User.is_active.is_(True),
    ).first()

    if not recruiter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Recruiter Not found")

    new_job = Job(
        **job_data.model_dump(),
        created_by=current_user.id,
        status="open",
        is_active=True
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    clear_job_cache()

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
