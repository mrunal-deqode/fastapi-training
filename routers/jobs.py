
from fastapi import APIRouter, HTTPException, Header, Response, status, Query, Depends

from models.schemas import JobCreate, JobResponse
from sqlalchemy.orm import Session
from database import get_db
from models.orm import Job, User

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


@router.get("", response_model=list[JobResponse])
def list_jobs(job_type: str | None = Query(default=None, min_length=2, max_length=30), db: Session = Depends(get_db)):
    query = db.query(Job).filter(
        Job.is_active.is_(True),
        Job.status == "open"
    )

    if job_type:
        query = query.filter(Job.job_type.ilike(job_type))

    return query.all()


@router.get("/manage", response_model=list[JobResponse])
def get_all_job_for_admin(created_by: int, db: Session = Depends(get_db)):
    admin = db.query(User).filter(
        User.id == created_by,
        User.role == "admin",
        User.is_active.is_(True)
    ).first()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")

    jobs = db.query(Job).filter(Job.created_by == created_by).all()

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


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_job(job_data: JobCreate, created_by: int, db: Session = Depends(get_db)):
    recruiter = db.query(User).filter(
        User.id == created_by,
        User.role == "admin",
        User.is_active.is_(True),
    ).first()

    if not recruiter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Recruiter Not found")

    new_job = Job(
        **job_data.model_dump(),
        created_by=created_by,
        status="open",
        is_active=True
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

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
