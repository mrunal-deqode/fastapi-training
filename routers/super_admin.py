
from fastapi import APIRouter, Depends, HTTPException, status
from models.schemas import (AdminCreate, AdminCreateResopnse, CandidateResponse, JobCreate,
                            JobResponse, JobStatusUpdate)
from sqlalchemy.orm import Session
from database import get_db
from models.orm import Job, User
from utils.security import hash_password
from utils.dependencies import require_roles
from utils.module7_dependencies import Pagination

router = APIRouter(prefix="/super-admin", tags=["Super Admin"])


@router.post("/create-admin", response_model=AdminCreateResopnse, status_code=status.HTTP_201_CREATED)
def create_admin(data: AdminCreate, current_user: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
    existing_admin = db.query(User).filter(User.email == data.email).first()

    if existing_admin:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="User with same details is already Registered")

    new_admin = User(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        hashed_password=hash_password(data.password),
        role="admin",
        is_active=True
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return new_admin


@router.get("/get-admins", response_model=list[AdminCreateResopnse])
def get_all_admins(current_user: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
    admins = db.query(User).filter(User.role == "admin").all()

    return admins


@router.get("/get-admin-details", response_model=AdminCreateResopnse)
def get_admin_details(admin_id: int, current_user: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
    admin_details = db.query(User).filter(
        User.id == admin_id, User.role == "admin").first()

    if not admin_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User Details not Exist")

    return admin_details


@router.patch("/deactivate-admin")
def deactivate_admin(admin_id: int, super_admin: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
    admin_details = db.query(User).filter(
        User.id == admin_id, User.role == "admin").first()

    if not admin_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User Details not Exist")

    if not admin_details.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Admin already Deactivated")

    admin_details.is_active = False

    db.commit()

    return {
        "message": "Admin Deacticated Succesfully",
    }


@router.patch("/reactivate-admin")
def reacticate_admin(admin_id: int, super_admin: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
    admin_details = db.query(User).filter(
        User.id == admin_id, User.role == "admin").first()

    if not admin_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User Details not Exist")

    if admin_details.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Admin already Activated")

    admin_details.is_active = True

    db.commit()

    return {"message": "Admin Acticated Succesfully"}


@router.get("/get-candidates", response_model=list[CandidateResponse])
def get_all_candidates(current_user: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db), pagination_data: Pagination = Depends(Pagination)):
    user_details = db.query(User).filter(User.role == "candidate").offset(
        pagination_data.skip).limit(pagination_data.limit).all()

    return user_details


@router.get("/get-candidate-details", response_model=CandidateResponse)
def get_candidate_details(user_id: int, current_user: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
    user_details = db.query(User).filter(
        User.id == user_id, User.role == "candidate").first()

    if not user_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User details not Found")

    return user_details


@router.patch("/deactivate-candidate")
def deactivate_candidate(user_id: int, current_user: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
    user_details = db.query(User).filter(
        User.id == user_id, User.role == "candidate").first()

    if not user_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User Details not Exist")

    if not user_details.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="User already Deactivated")

    user_details.is_active = False

    db.commit()

    return {
        "message": "User Deactivated Succesfully",
    }


@router.patch("/reactivate-candidate")
def reacticate_candidate(user_id: int, current_user: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
    user_details = db.query(User).filter(
        User.id == user_id, User.role == "candidate").first()

    if not user_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User Details not Exist")

    if user_details.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="User already Activated")

    user_details.is_active = True

    db.commit()

    return {"message": "User Activated Succesfully"}


@router.get("/get-jobs", response_model=list[JobResponse])
def get_all_jobs(current_user: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
    job_list = db.query(Job).all()

    return job_list


@router.get("/get-job-detail", response_model=JobResponse)
def get_job_details(job_id: int, current_user: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
    job_detail = db.query(Job).filter(Job.id == job_id).first()

    if not job_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job details not found")

    return job_detail


@router.put("/update-job", response_model=JobResponse)
def update_any_job(job_id: int, data: JobCreate, current_user: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
    existing_job = db.query(Job).filter(
        Job.id == job_id, Job.is_active.is_(True)).first()

    if not existing_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job details not found")

    existing_job.title = data.title
    existing_job.description = data.description
    existing_job.job_type = data.job_type
    existing_job.deadline = data.deadline
    existing_job.location = data.location
    existing_job.min_experience_years = data.min_experience_years
    existing_job.max_experience_years = data.max_experience_years
    existing_job.salary_min = data.salary_min
    existing_job.salary_max = data.salary_max

    db.commit()
    db.refresh(existing_job)

    return existing_job


@router.patch("/update-status", response_model=JobResponse)
def update_job_status(job_id: int, data: JobStatusUpdate, current_user: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id,
                               Job.is_active.is_(True)).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job Details not Found")

    if job.status == data.status:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Job is already {data.status}")

    job.status = data.status

    db.commit()
    db.refresh(job)

    return job


# @router.post("/create-super-admin", response_model=AdminCreateResopnse)
# def create_super_admin(data: AdminCreate, current_user: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
#     existing_super_admin = db.query(User).filter(
#         User.email == data.email).first()

#     if existing_super_admin:
#         raise HTTPException(status_code=status.HTTP_409_CONFLICT,
#                             detail="User already registered")

#     new_super_admin = User(
#         full_name=data.full_name,
#         email=data.email,
#         hashed_password=hash_password(data.password),
#         phone=data.phone,
#         role="super_admin",
#         is_active=True
#     )

#     db.add(new_super_admin)
#     db.commit()
#     db.refresh(new_super_admin)

#     return new_super_admin
