
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from database import get_db
from models.orm import Job, User
from models.schemas import (
    JobCreate,
    JobInfoResponse,
    JobResponse,
    PaginationResponse,
)
from redis_client import clear_dashboard_cache, clear_job_cache, redis_client
from utils.dependencies import require_roles
from utils.module7_dependencies import PagePagination

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


@router.get(
    "",
    response_model=PaginationResponse[JobResponse],
    summary="List available job openings",
    description=(
        "Returns active job openings with open status. "
        "Supports optional job-type filtering and page-based pagination. "
        "Results are cached in Redis for improved performance."
    ),
    responses={
        200: {
            "description": "Paginated list of available jobs",
            "content": {
                "application/json": {
                    "example": {
                        "total": 25,
                        "page": 1,
                        "limit": 10,
                        "items": [
                            {
                                "id": 1,
                                "title": "Python Backend Developer",
                                "description": "Develop backend services using FastAPI.",
                                "job_type": "Full-time",
                                "deadline": "2026-12-31",
                                "location": "Indore",
                                "min_experience_years": 1,
                                "max_experience_years": 3,
                                "salary_min": 300000,
                                "salary_max": 600000,
                                "status": "open",
                                "is_active": True
                            }
                        ]
                    }
                }
            }
        },
        422: {"description": "Invalid query parameters"}
    }
)
def list_jobs(
    job_type: str | None = Query(default=None, min_length=2, max_length=30),
    db: Session = Depends(get_db),
    pagination: PagePagination = Depends(PagePagination),
):
    cache_key = (
        f"jobs:list:{job_type or 'all'}:"
        f"{pagination.page}:{pagination.limit}"
    )

    cached_jobs = redis_client.get(cache_key)

    if cached_jobs:
        return json.loads(cached_jobs)

    query = db.query(Job).filter(
        Job.is_active.is_(True),
        Job.status == "open"
    )

    if job_type:
        query = query.filter(Job.job_type.ilike(job_type))

    total = query.count()

    jobs = query.offset(pagination.skip).limit(pagination.limit).all()

    jobs_data = [
        JobResponse.model_validate(job).model_dump(mode="json")
        for job in jobs
    ]

    response_data = {
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit,
        "items": jobs_data,
    }

    redis_client.setex(cache_key, 60, json.dumps(response_data))

    return response_data


@router.get(
    "/manage",
    response_model=PaginationResponse[JobResponse],
    summary="List jobs created by the admin",
    description=(
        "Returns all job openings created by the currently authenticated admin. "
        "Requires admin role authorization."
    ),
    responses={
        200: {
            "description": "Admin job listings retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "title": "Python Backend Developer",
                            "description": "Develop backend services using FastAPI.",
                            "job_type": "Full-time",
                            "deadline": "2026-12-31",
                            "location": "Indore",
                            "min_experience_years": 1,
                            "max_experience_years": 3,
                            "salary_min": 300000,
                            "salary_max": 600000,
                            "status": "open",
                            "is_active": True
                        }
                    ]
                }
            }
        },
        401: {"description": "Authentication required"},
        403: {"description": "Admin access required"}
    }
)
def get_all_job_for_admin(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
    pagination: PagePagination = Depends(PagePagination),
):
    query = db.query(Job).filter(
        Job.created_by == current_user.id
    )

    total = query.count()

    jobs = (
        query.offset(pagination.skip)
        .limit(pagination.limit)
        .all()
    )

    return {
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit,
        "items": jobs,
    }


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job details",
    description=(
        "Retrieves a specific active job opening using its ID. "
        "Only jobs with open status are returned. "
        "Returns 404 if the job does not exist or is unavailable."
    ),
    responses={
        200: {
            "description": "Job details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Python Backend Developer",
                        "description": "Develop backend services using FastAPI.",
                        "job_type": "Full-time",
                        "deadline": "2026-12-31",
                        "location": "Indore",
                        "min_experience_years": 1,
                        "max_experience_years": 3,
                        "salary_min": 300000,
                        "salary_max": 600000,
                        "status": "open",
                        "is_active": True
                    }
                }
            }
        },
        404: {
            "description": "Job not found or unavailable"
        },
        422: {
            "description": "Invalid job ID"
        }
    }
)
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


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job opening",
    description=(
        "Allows an authenticated admin to publish a new job opening. "
        "The job is created with an open status and active state. "
        "The job listing cache is cleared after successful creation."
    ),
    responses={
        201: {
            "description": "Job created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Python Backend Developer",
                        "description": "Develop and maintain backend services using Python and FastAPI.",
                        "job_type": "Full-time",
                        "deadline": "2026-12-31",
                        "location": "Indore",
                        "min_experience_years": 1,
                        "max_experience_years": 3,
                        "salary_min": 300000,
                        "salary_max": 600000,
                        "status": "open",
                        "is_active": True
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        403: {"description": "Admin access required"},
        404: {"description": "Recruiter not found"},
        422: {"description": "Invalid job data"},
    },
)
def create_job(
    job_data: JobCreate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
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
    clear_dashboard_cache(current_user.id)
    db.refresh(new_job)

    clear_job_cache()

    return new_job


@router.get(
    "/{job_id}/info",
    summary="Get job access information",
    description=(
        "Returns the requested job ID and the client's User-Agent. "
        "Also includes an X-Job-Id response header and stores the "
        "last viewed job ID in a cookie named last_viewed_job."
    ),
    responses={
        200: {
            "description": "Job access information retrieved",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": 1,
                        "your_user_agent": "Mozilla/5.0"
                    }
                }
            },
            "headers": {
                "X-Job-Id": {
                    "description": "ID of the viewed job",
                    "schema": {"type": "string"},
                    "example": "1"
                },
                "Set-Cookie": {
                    "description": "Stores the last viewed job ID",
                    "schema": {"type": "string"},
                    "example": "last_viewed_job=1"
                }
            }
        },
        422: {"description": "Invalid job ID"}
    },
    openapi_extra={
        "x-client-notes": (
            "The last_viewed_job cookie is updated whenever this endpoint is called."
        )
    },
    response_model=JobInfoResponse,
)
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
