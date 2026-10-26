from fastapi import FastAPI

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