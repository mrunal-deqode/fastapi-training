from fastapi import FastAPI
from pydantic import BaseModel

class ApplicationCreate(BaseModel):
    candidate_name:str
    job_title:str

app = FastAPI()


applications = [
    {"id": 1, "candidate_name": "Asha Verma", "job_title": "Backend Developer", "status": "Applied"},
    {"id": 2, "candidate_name": "Rohan Mehta", "job_title": "QA Engineer", "status": "Resume Viewed"},
    {"id": 3, "candidate_name": "Neha Singh", "job_title": "Backend Developer", "status": "Shortlisted"},
]


@app.get("/applications")
def list_applications():
    return applications

@app.get("/applications/{application_id}")
def get_application(application_id: int):
    for application in applications:
        if application["id"] == application_id:
            return application
    return {"error": "Application not found"}

@app.post("/application")
def create_application(application : ApplicationCreate):
    new_application = {
        "id" : len(applications)+1,
        "candidate_name": application.candidate_name,
        "job_title": application.job_title,
        "status" : "applied"
    }
    applications.append(new_application)
    return new_application