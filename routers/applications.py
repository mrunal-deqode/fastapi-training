
from fastapi import APIRouter, HTTPException, status

from models.schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    StatusUpdate,
)

router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)

applications = [
    {
        "id": 1,
        "candidate_name": "Asha Verma",
        "job_title": "Backend Developer",
        "status": "Applied",
    },
    {
        "id": 2,
        "candidate_name": "Rohan Mehta",
        "job_title": "QA Engineer",
        "status": "Under Review",
    },
    {
        "id": 3,
        "candidate_name": "Neha Singh",
        "job_title": "Backend Developer",
        "status": "Shortlisted",
    },
]


def find_application(application_id: int):
    for application in applications:
        if application["id"] == application_id:
            return application

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Application not found",
    )


@router.get("", response_model=list[ApplicationResponse])
def list_applications():
    return applications


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
)
def get_application(application_id: int):
    return find_application(application_id)


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_application(application: ApplicationCreate):
    new_application = {
        "id": max(
            (item["id"] for item in applications),
            default=0,
        ) + 1,
        "candidate_name": application.candidate_name,
        "job_title": application.job_title,
        "contact": application.contact.model_dump(),
        "years_of_experience": application.years_of_experience,
        "status": "Applied",
    }

    applications.append(new_application)
    return new_application


@router.put(
    "/{application_id}",
    response_model=ApplicationResponse,
)
def replace_application(
    application_id: int,
    data: ApplicationCreate,
):
    application = find_application(application_id)

    application.update({
        "candidate_name": data.candidate_name,
        "job_title": data.job_title,
        "contact": data.contact.model_dump(),
        "years_of_experience": data.years_of_experience,
    })

    return application


@router.patch(
    "/{application_id}",
    response_model=ApplicationResponse,
)
def update_application(
    application_id: int,
    data: ApplicationUpdate,
):
    application = find_application(application_id)

    changes = data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    application.update(changes)
    return application


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationResponse,
)
def update_status(
    application_id: int,
    data: StatusUpdate,
):
    application = find_application(application_id)
    application["status"] = data.status

    return application


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_application(application_id: int):
    application = find_application(application_id)
    applications.remove(application)
