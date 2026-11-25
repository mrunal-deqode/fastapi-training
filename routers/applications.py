
import hashlib
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models.orm import Application, IdempotencyRecord, Job, User
from models.schemas import (
    AdminApplicantDetailResponse,
    ApplicantDetailsResponse,
    ApplicationReplace,
    ApplicationResponse,
    ApplicationStatus,
    ApplicationUpdate,
    CandidateApplicationCreate,
    PaginationResponse,
    StatusUpdate,
)

# import time
from tasks import send_application_status_email
from utils.dependencies import get_authorized_application, require_roles
from utils.module7_dependencies import PagePagination

router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a job application",
    description=(
        "Allows an authenticated candidate to apply for an active job. "
        "Supports Idempotency-Key to safely retry requests."
    ),
)
def create_application(
    data: CandidateApplicationCreate,
    current_user: User = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        max_length=255,
    ),
):
    request_hash = hashlib.sha256(
        json.dumps(
            data.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()

    # 1. Check whether this request was already processed.
    if idempotency_key:
        existing_record = db.query(IdempotencyRecord).filter(
            IdempotencyRecord.candidate_id == current_user.id,
            IdempotencyRecord.idempotency_key == idempotency_key,
        ).first()

        if existing_record:
            if existing_record.request_hash != request_hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key reused with different request data",
                )

            return existing_record.response_body

    # 2. Validate the job.
    job = db.query(Job).filter(
        Job.id == data.job_id,
        Job.is_active.is_(True),
        Job.status == "open",
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active open job not found",
        )

    # 3. Preserve existing duplicate application protection.
    existing_application = db.query(Application).filter(
        Application.candidate_id == current_user.id,
        Application.job_id == data.job_id,
    ).first()

    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Candidate has already applied for this job",
        )

    # 4. Create the application and save its original response.
    new_application = Application(
        candidate_id=current_user.id,
        job_id=data.job_id,
        years_of_experience=data.years_of_experience,
        cover_letter=data.cover_letter,
    )

    try:
        db.add(new_application)
        db.flush()
        db.refresh(new_application)

        response_body = {
            "id": new_application.id,
            "candidate_id": new_application.candidate_id,
            "job_id": new_application.job_id,
            "years_of_experience": new_application.years_of_experience,
            "cover_letter": new_application.cover_letter,
            "status": new_application.status,
            "is_active": new_application.is_active,
        }

        if idempotency_key:
            db.add(
                IdempotencyRecord(
                    candidate_id=current_user.id,
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    response_body=response_body,
                    response_status_code=status.HTTP_201_CREATED,
                )
            )

        db.commit()

    except IntegrityError:
        db.rollback()

        # Handle concurrent retries using the same key.
        if idempotency_key:
            existing_record = db.query(IdempotencyRecord).filter(
                IdempotencyRecord.candidate_id == current_user.id,
                IdempotencyRecord.idempotency_key == idempotency_key,
            ).first()

            if existing_record:
                if existing_record.request_hash == request_hash:
                    return existing_record.response_body

                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key reused with different request data",
                )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Application already exists",
        )

    return response_body if idempotency_key else new_application


@router.get(
    "",
    response_model=PaginationResponse[ApplicationResponse],
    summary="List all active applications",
    description=(
        "Returns active job applications across the recruitment system "
        "using page-based pagination. Accessible only to super administrators."
    ),
)
def get_applications(
    current_user: User = Depends(require_roles("super_admin")),
    db: Session = Depends(get_db),
    pagination: PagePagination = Depends(PagePagination),
):
    query = db.query(Application).filter(
        Application.is_active.is_(True)
    )

    total = query.count()

    applications = (
        query.offset(pagination.skip)
        .limit(pagination.limit)
        .all()
    )

    return {
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit,
        "items": applications,
    }


@router.get(
    "/my-applications",
    response_model=PaginationResponse[ApplicationResponse],
    summary="List my job applications",
    description=(
        "Returns active applications submitted by the authenticated "
        "candidate using page-based pagination."
    ),
)
def get_my_application(
    current_user: User = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
    pagination: PagePagination = Depends(PagePagination),
    status_filter: ApplicationStatus | None = Query(
        default=None, alias="status"),
    job_id: int | None = Query(default=None, gt=0),
):
    query = db.query(Application).filter(
        Application.candidate_id == current_user.id,
        Application.is_active.is_(True),
    )

    if status_filter is not None:
        query = query.filter(Application.status == status_filter)

    if job_id is not None:
        query = query.filter(Application.job_id == job_id)

    total = query.count()

    applications = (
        query.order_by(Application.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
        .all()
    )

    return {
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit,
        "items": applications,
    }


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Get application details",
    description=(
        "Retrieves an active job application by its ID. "
        "The endpoint requires an authenticated user with permission "
        "to access the application."
    ),
    responses={
        200: {
            "description": "Application details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "candidate_id": 10,
                        "job_id": 5,
                        "years_of_experience": 2.0,
                        "cover_letter": "I have experience with Python and FastAPI.",
                        "status": "Applied",
                        "is_active": True
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        403: {"description": "Access denied"},
        404: {"description": "Application not found"},
        422: {"description": "Invalid application ID"}
    }
)
def get_application(
    application: Application = Depends(get_authorized_application),
):
    return application


@router.put(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Replace an existing application",
    description=(
        "Replaces the application details using the complete request body. "
        "The candidate ID, job ID, and years of experience are required. "
        "The endpoint validates the candidate and job and prevents duplicate applications."
    ),
    responses={
        200: {
            "description": "Application replaced successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "candidate_id": 10,
                        "job_id": 5,
                        "years_of_experience": 3.0,
                        "cover_letter": "Updated experience in backend development.",
                        "status": "Applied",
                        "is_active": True
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        403: {"description": "Access denied"},
        404: {"description": "Application, candidate, or job not found"},
        409: {"description": "Duplicate application"},
        422: {"description": "Invalid replacement data"}
    }
)
def replace_application(
    data: ApplicationReplace,
    application: Application = Depends(get_authorized_application),
    db: Session = Depends(get_db),
):
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


@router.patch(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Update application details",
    description=(
        "Partially updates an existing application. "
        "Only years_of_experience and cover_letter can be updated. "
        "At least one update field must be provided."
    ),
    responses={
        200: {
            "description": "Application updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "candidate_id": 10,
                        "job_id": 5,
                        "years_of_experience": 3.0,
                        "cover_letter": "Updated backend development experience.",
                        "status": "Applied",
                        "is_active": True
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        403: {"description": "Access denied"},
        404: {"description": "Application not found"},
        422: {"description": "Invalid update data"}
    }
)
def update_application(
    data: ApplicationUpdate,
    application: Application = Depends(get_authorized_application),
    db: Session = Depends(get_db),
):
    changes = data.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    if "years_of_experience" in changes:
        if changes["years_of_experience"] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Years of experience cannot be null",
            )

        application.years_of_experience = changes["years_of_experience"]

    if "cover_letter" in changes:
        application.cover_letter = changes["cover_letter"]

    db.commit()
    db.refresh(application)

    return application


@router.delete(
    "/{application_id}",
    status_code=204,
    summary="Delete an application",
    description=(
        "Soft-deletes an application by setting is_active to false. "
        "The application record remains in the database and is not permanently deleted."
    ),
    responses={
        204: {
            "description": "Application deleted successfully. No response body is returned."
        },
        401: {"description": "Authentication required"},
        403: {"description": "Access denied"},
        404: {"description": "Application not found"},
        422: {"description": "Invalid application ID"}
    }
)
def delete_application(
    application: Application = Depends(get_authorized_application),
    db: Session = Depends(get_db),
):
    application.is_active = False

    db.commit()

    return None


@router.get(
    "/admin/jobs/{job_id}/appliactions",
    response_model=PaginationResponse[ApplicantDetailsResponse],
    summary="List applicants for a job",
    description=(
        "Returns applicant details for a specific job. "
        "Accessible to administrators authorized to manage the job."
    ),
    responses={
        200: {
            "description": "Applicants retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "total": 1,
                        "page": 1,
                        "limit": 10,
                        "items": [
                            {
                                "application_id": 1,
                                "candidate_id": 10,
                                "candidate_name": "Rahul Sharma",
                                "candidate_email": "rahul@example.com",
                                "candidate_phone": "9876543210",
                                "years_of_experience": 2.0,
                                "cover_letter": "I have experience building REST APIs.",
                                "status": "Applied"
                            }
                        ]
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        403: {"description": "Administrator access denied"},
        404: {"description": "Job not found"},
        422: {"description": "Invalid job ID"}
    }
)
def get_job_applications(
    job_id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
    pagination: PagePagination = Depends(PagePagination),
    status_filter: ApplicationStatus | None = Query(
        default=None, alias="status"
    ),
):
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.is_active.is_(True),
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jobs Not Found",
        )

    if job.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view applicants for this job",
        )

    query = db.query(Application).options(
        selectinload(Application.candidate)
    ).join(
        User, Application.candidate_id == User.id
    ).filter(
        Application.job_id == job_id,
        Application.is_active.is_(True),
    )

    if status_filter is not None:
        query = query.filter(Application.status == status_filter)

    total = query.count()

    applications = (
        query.order_by(Application.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
        .all()
    )

    items = [
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

    return {
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit,
        "items": items,
    }


@router.get(
    "/admin/applications/{application_id}",
    response_model=AdminApplicantDetailResponse,
    summary="Get applicant details for an administrator",
    description=(
        "Retrieves detailed information about an applicant, including "
        "contact details, education, experience, skills, and resume URL. "
        "Accessible only to an administrator authorized to view the application."
    ),
    responses={
        200: {
            "description": "Applicant details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "application_id": 1,
                        "job_id": 5,
                        "candidate_id": 10,
                        "candidate_name": "Rahul Sharma",
                        "candidate_email": "rahul@example.com",
                        "candidate_phone": "9876543210",
                        "years_of_experience": 2.0,
                        "cover_letter": "I have experience building REST APIs.",
                        "status": "Applied",
                        "education": "MCA",
                        "experience": "2 years of backend development",
                        "skills": "Python, FastAPI, PostgreSQL",
                        "resume_url": "https://example.com/resume.pdf"
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        403: {"description": "Administrator access denied"},
        404: {"description": "Application not found"},
        422: {"description": "Invalid application ID"}
    }
)
def get_admin_applicant_details(application_id: int, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):

    application = db.query(Application).filter(
        Application.id == application_id,
        Application.is_active.is_(True),
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    if application.job.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this application",
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


@router.patch(
    "/admin/applications/{application_id}/status",
    response_model=ApplicationResponse,
    summary="Update application status",
    description=(
        "Updates an applicant's status for a job application. "
        "The status must be one of: Applied, Under Review, Shortlisted, "
        "Selected, or Rejected. The update also triggers an email notification."
    ),
    responses={
        200: {
            "description": "Application status updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "candidate_id": 10,
                        "job_id": 5,
                        "years_of_experience": 2.0,
                        "cover_letter": "I have experience building REST APIs.",
                        "status": "Shortlisted",
                        "is_active": True
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        403: {"description": "Administrator access denied"},
        404: {"description": "Application not found"},
        422: {"description": "Invalid application status"}
    }
)
def update_application_status(application_id: int, data: StatusUpdate, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):

    application = db.query(Application).filter(
        Application.id == application_id,
        Application.is_active.is_(True),
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    if application.job.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this application",
        )

    application.status = data.status

    db.commit()
    db.refresh(application)

    send_application_status_email.delay(
        application.candidate.email,
        application.candidate.full_name,
        application.job.title,
        application.status
    )

    return application


# async def send_application_status_notification(candidate_email: str, candidate_name: str, job_title: str, application_stauts: str):
#     # time.sleep(3)
#     subject = f"Application Update - {job_title}"

#     body = f"""
#         Hello {candidate_name},

#         We have an update regarding your job application.

#         Job Title: {job_title}
#         Current Application Status: {application_stauts}

#         Please log in to your Recruitment & Hiring account
#         to check your application details.

#         Thank you,
#         Recruitment & Hiring Team
#         """

#     await send_email(recipient=candidate_email, subject=subject, body=body)
