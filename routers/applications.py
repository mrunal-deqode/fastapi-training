
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models.orm import Application, User, Job
from models.schemas import (AdminApplicantDetailResponse, ApplicantDetailsResponse,
                            ApplicationReplace, ApplicationResponse, ApplicationUpdate,
                            CandidateApplicationCreate, StatusUpdate)
from utils.dependencies import require_roles
from utils.module7_dependencies import pagniation
import time

router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(data: CandidateApplicationCreate, current_user: User = Depends(require_roles("candidate")), db: Session = Depends(get_db)):
    job = db.query(Job).filter(
        Job.id == data.job_id,
        Job.is_active == True,
        Job.status == "open",
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active open job not found",
        )

    existing_application = db.query(Application).filter(
        Application.candidate_id == current_user.id,
        Application.job_id == data.job_id,
    ).first()

    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Candidate has already applied for this job",
        )

    new_application = Application(
        candidate_id=current_user.id,
        job_id=data.job_id,
        years_of_experience=data.years_of_experience,
        cover_letter=data.cover_letter,
    )

    try:
        db.add(new_application)
        db.commit()
        db.refresh(new_application)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Application already exists",
        )

    return new_application


@router.get("", response_model=list[ApplicationResponse])
def get_applications(current_user: User = Depends(require_roles("super_admin")), db: Session = Depends(get_db)):
    applications = db.query(Application).filter(
        Application.is_active == True
    ).all()

    return applications


@router.get("/my-applications", response_model=list[ApplicationResponse])
def get_my_application(current_user: User = Depends(require_roles("candidate")), db: Session = Depends(get_db), pagination_data: dict = Depends(pagniation)):

    application = db.query(Application).filter(
        Application.candidate_id == current_user.id,
        Application.is_active.is_(True)
    ).offset(pagination_data["skip"]).limit(pagination_data["limit"]).all()

    return application


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
)
def get_application(application_id: int, db: Session = Depends(get_db)):
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.is_active == True,
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    return application


@router.put(
    "/{application_id}",
    response_model=ApplicationResponse,
)
def replace_application(application_id: int, data: ApplicationReplace, db: Session = Depends(get_db)):
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.is_active == True,
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    candidate = db.query(User).filter(
        User.id == data.candidate_id,
        User.role == "candidate",
        User.is_active == True,
    ).first()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active candidate not found",
        )

    job = db.query(Job).filter(
        Job.id == data.job_id,
        Job.is_active == True,
        Job.status == "open",
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active open job not found",
        )

    existing_application = db.query(Application).filter(
        Application.candidate_id == data.candidate_id,
        Application.job_id == data.job_id,
        Application.id != application_id,
    ).first()

    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Candidate has already applied for this job",
        )

    application.candidate_id = data.candidate_id
    application.job_id = data.job_id
    application.years_of_experience = data.years_of_experience
    application.cover_letter = data.cover_letter

    try:
        db.commit()
        db.refresh(application)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Application conflicts with an existing record",
        )

    return application


@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    data: ApplicationUpdate,
    db: Session = Depends(get_db)
):
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.is_active == True
    ).first()

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    changes = data.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUESTS,
            detail="No fields provided for update"
        )

    if "years_of_experience" in changes:
        if changes["years_of_experience"] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Years of experience cannot be null"
            )

        application.years_of_experience = changes["years_of_experience"]

    if "cover_letter" in changes:
        application.cover_letter = changes["cover_letter"]

    db.commit()
    db.refresh(application)

    return application


@router.delete("/{application_id}", status_code=204)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db)
):
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.is_active == True
    ).first()

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    application.is_active = False

    db.commit()

    return None


@router.get("/admin/jobs/{job_id}/appliactions", response_model=list[ApplicantDetailsResponse])
def get_job_applications(job_id: int, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):

    jobs = db.query(Job).filter(
        Job.id == job_id,
        Job.created_by == current_user.id
    ).first()

    if not jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Jobs Not Found")

    applications = db.query(Application).join(
        User, Application.candidate_id == User.id
    ).filter(
        Application.job_id == job_id,
        Application.is_active.is_(True)
    ).all()

    return [
        {
            "application_id": application.id,
            "candidate_id": application.candidate_id,
            "candidate_name": application.candidate.full_name,
            "candidate_email": application.candidate.email,
            "candidate_phone": application.candidate.phone,
            "years_of_experience": application.years_of_experience,
            "cover_letter": application.cover_letter,
            "status": application.status,
        }
        for application in applications
    ]


@router.get("/admin/applications/{application_id}", response_model=AdminApplicantDetailResponse)
def get_admin_applicant_details(application_id: int, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):

    application = db.query(Application).join(
        Job,
        Application.job_id == Job.id,
    ).filter(
        Application.id == application_id,
        Application.is_active.is_(True),
        Job.created_by == current_user.id,
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or you don't have permission to view it",
        )

    candidate = application.candidate
    profile = candidate.profile

    return {
        "application_id": application.id,
        "job_id": application.job_id,
        "candidate_id": candidate.id,
        "candidate_name": candidate.full_name,
        "candidate_email": candidate.email,
        "candidate_phone": candidate.phone,
        "years_of_experience": application.years_of_experience,
        "cover_letter": application.cover_letter,
        "status": application.status,
        "education": profile.education if profile else None,
        "experience": profile.experience if profile else None,
        "skills": profile.skills if profile else None,
        "resume_url": profile.resume_url if profile else None,
    }


@router.patch("/admin/applications/{application_id}/status", response_model=ApplicationResponse)
def update_application_status(application_id: int, data: StatusUpdate, background_task: BackgroundTasks, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    application = db.query(Application).join(
        Job,
        Application.job_id == Job.id
    ).filter(
        Application.id == application_id,
        Application.is_active.is_(True),
        Job.created_by == current_user.id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or you don't have permission to update it"
        )

    application.status = data.status

    db.commit()
    db.refresh(application)

    background_task.add_task(send_application_status_notification,
                             application.candidate.email, application.job.title, application.status)

    return application


def send_application_status_notification(candidate_email: str, job_title: str, application_stauts: str):
    time.sleep(3)

    print(
        f"Notification sent to {candidate_email}, For Application {job_title}, changed status {application_stauts}")
