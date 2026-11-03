
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models.orm import Application, User, Job
from models.schemas import (ApplicantDetailsResponse, ApplicationCreate, ApplicationReplace,
                            ApplicationResponse, ApplicationUpdate, StatusUpdate)

router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    data: ApplicationCreate,
    db: Session = Depends(get_db),
):
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
    ).first()

    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Candidate has already applied for this job",
        )

    new_application = Application(
        candidate_id=data.candidate_id,
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


@router.get(
    "",
    response_model=list[ApplicationResponse],
)
def get_applications(db: Session = Depends(get_db)):
    applications = db.query(Application).filter(
        Application.is_active == True
    ).all()

    return applications


@router.get("/my-applications", response_model=list[ApplicationResponse])
def get_my_application(user_id: int, db: Session = Depends(get_db)):
    candidate = db.query(User).filter(
        User.id == user_id,
        User.role == "candidate",
        User.is_active == True,
    ).first()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active candidate not found",
        )

    application = db.query(Application).filter(
        Application.candidate_id == user_id,
        Application.is_active.is_(True)
    ).all()

    return application


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
):
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
def replace_application(
    application_id: int,
    data: ApplicationReplace,
    db: Session = Depends(get_db),
):
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
            status_code=400,
            detail="No fields provided for update"
        )

    if "years_of_experience" in changes:
        if changes["years_of_experience"] is None:
            raise HTTPException(
                status_code=422,
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
def get_job_applications(job_id: int, admin_id: int, db: Session = Depends(get_db)):
    admin = db.query(User).filter(
        User.id == admin_id,
        User.role == "admin",
        User.is_active.is_(True)
    ).first()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")

    jobs = db.query(Job).filter(
        Job.id == job_id,
        Job.created_by == admin_id
    ).all()

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
