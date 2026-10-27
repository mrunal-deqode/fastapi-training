from typing import List
from fastapi import APIRouter, HTTPException, status
from models.schemas import (
    ApplicationResponse,
    ApplicationCreate,
    ApplicationUpdate,
    StatusUpdate
)

router = APIRouter(prefix="/applications", tags=["Applications"])

STATUS=["Applied", "Resume Viewed", "Shortlisted", "Rejected", "Contacted by Email"]

applications = [
    {"id": 1, "candidate_name": "Asha Verma", "job_title": "Backend Developer", "status": "Applied"},
    {"id": 2, "candidate_name": "Rohan Mehta", "job_title": "QA Engineer", "status": "Resume Viewed"},
    {"id": 3, "candidate_name": "Neha Singh", "job_title": "Backend Developer", "status": "Shortlisted"},
]

def find_application(application_id:int):
    for application in applications:
        if application["id"]==application_id:
            return application
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application Not found")


@router.get("", response_model=List[ApplicationResponse])
def list_application():
    return applications

@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(application_id:int):
    return find_application(application_id)

@router.post("",response_model=ApplicationCreate, status_code=status.HTTP_201_CREATED)
def create_application(application:ApplicationCreate):
    new_application={
        "id":len(applications)+1,
        "candidate_name": application.candidate_name,
        "job_title": application.job_title,
        "contact": application.contact.model_dump(),
        "years_of_experience": application.years_of_experience,
        "status": "Applied"
    }
    
    applications.append(new_application)
    return new_application

@router.put("/{application_id}",response_model=ApplicationCreate)
def replace_application(application_id:int, data:ApplicationCreate):
    print("before find_application")
    application = find_application(application_id)
    print("after find_application")
    application["candidate_name"]=data.candidate_name
    application["job_title"]=data.job_title
    application["contact"]=data.contact.model_dump()
    application["years_of_experience"]=data.years_of_experience
    
    return application

@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application(application_id: int, data: ApplicationUpdate):
    application = find_application(application_id)
    changes = data.model_dump(exclude_unset=True)
    application.update(changes)
    return application

@router.patch("/{application_id}/status")
def update_status(application_id:int, data:StatusUpdate):
    if data.status not in STATUS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Statuis")
    application = find_application(application_id)
    application["status"]=data.status
    return application

@router.delete("/{application_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_application(application_id:int):
    application = find_application(application_id)
    applications.remove(application)