import json

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models.orm import Application, Job, User
from models.schemas import (
    AdminDashboardResponse,
    CandidateDashboardResponse,
)
from redis_client import redis_client
from utils.dependencies import require_roles

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/candidate",
    response_model=CandidateDashboardResponse,
)
def candidate_dashboard(
    current_user: User = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    cache_key = f"dashboard:{current_user.id}:candidate"

    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    base_query = db.query(Application).filter(
        Application.candidate_id == current_user.id,
        Application.is_active.is_(True),
    )

    total_applications = base_query.count()

    status_counts = {
        "Applied": 0,
        "Under Review": 0,
        "Shortlisted": 0,
        "Selected": 0,
        "Rejected": 0,
    }

    counts = (
        db.query(Application.status, func.count(Application.id))
        .filter(
            Application.candidate_id == current_user.id,
            Application.is_active.is_(True),
        )
        .group_by(Application.status)
        .all()
    )

    for application_status, count in counts:
        status_counts[application_status] = count

    recent_applications = (
        db.query(Application, Job.title)
        .join(Job, Application.job_id == Job.id)
        .filter(
            Application.candidate_id == current_user.id,
            Application.is_active.is_(True),
        )
        .order_by(Application.created_at.desc())
        .limit(5)
        .all()
    )

    recent_data = [
        {
            "application_id": application.id,
            "job_id": application.job_id,
            "job_title": job_title,
            "status": application.status,
            "applied_at": application.created_at.isoformat(),
        }
        for application, job_title in recent_applications
    ]

    response_data = {
        "total_applications": total_applications,
        "status_counts": status_counts,
        "recent_applications": recent_data,
    }

    redis_client.setex(cache_key, 60, json.dumps(response_data))

    return response_data


@router.get(
    "/admin",
    response_model=AdminDashboardResponse,
)
def admin_dashboard(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    cache_key = f"dashboard:{current_user.id}:admin"

    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    jobs_query = db.query(Job).filter(
        Job.created_by == current_user.id,
        Job.is_active.is_(True),
    )

    total_jobs = jobs_query.count()

    application_query = (
        db.query(Application)
        .join(Job, Application.job_id == Job.id)
        .filter(
            Job.created_by == current_user.id,
            Application.is_active.is_(True),
        )
    )

    total_applications = application_query.count()

    status_counts = {
        "Applied": 0,
        "Under Review": 0,
        "Shortlisted": 0,
        "Selected": 0,
        "Rejected": 0,
    }

    counts = (
        db.query(Application.status, func.count(Application.id))
        .join(Job, Application.job_id == Job.id)
        .filter(
            Job.created_by == current_user.id,
            Application.is_active.is_(True),
        )
        .group_by(Application.status)
        .all()
    )

    for application_status, count in counts:
        status_counts[application_status] = count

    recent_applications = (
        db.query(Application, User.full_name, Job.title)
        .join(Job, Application.job_id == Job.id)
        .join(User, Application.candidate_id == User.id)
        .filter(
            Job.created_by == current_user.id,
            Application.is_active.is_(True),
        )
        .order_by(Application.created_at.desc())
        .limit(5)
        .all()
    )

    recent_data = [
        {
            "application_id": application.id,
            "candidate_id": application.candidate_id,
            "candidate_name": candidate_name,
            "job_id": application.job_id,
            "job_title": job_title,
            "status": application.status,
            "applied_at": application.created_at.isoformat(),
        }
        for application, candidate_name, job_title in recent_applications
    ]

    response_data = {
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "status_counts": status_counts,
        "recent_applicants": recent_data,
    }

    redis_client.setex(cache_key, 60, json.dumps(response_data))

    return response_data
