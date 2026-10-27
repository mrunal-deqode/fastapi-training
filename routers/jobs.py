from typing import List
from fastapi import APIRouter, HTTPException, status, Header, Response
from models.schemas import JobCreate, JobResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])

jobs = [
    {"id": 1, "title": "Backend Developer", "description": "Build and maintain REST APIs", "job_type": "Full-time", "deadline": "2026-12-31"},
    {"id": 2, "title": "QA Engineer", "description": "Test and verify product releases", "job_type": "Part-time", "deadline": "2026-11-30"},
]

@router.get("",response_model=List[JobResponse])
def list_jobs(job_type:str | None = None):
    if job_type:
        return [j for j in jobs if j["job_type"].lower() == job_type.lower()]
    return jobs

@router.get("/{job_id}",response_model=JobResponse)
def get_job(job_id:int):
    for job in jobs:
        if job["id"]==job_id:
            return job
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Id not found")

@router.post("",response_model=JobCreate, status_code=status.HTTP_201_CREATED)
def create_job(job:JobCreate):
    new_job={
        "id":len(jobs)+1,
        "title":job.title,
        "description":job.description,
        "job_type": job.job_type,
        "deadline": job.deadline
    }
    
    jobs.append(new_job)
    return new_job

@router.get("/{job_id}/info")
def job_info(job_id: int, response: Response, user_agent: str | None = Header(default=None)):
    response.headers["X-Job-Id"] = str(job_id)
    response.set_cookie(key="last_viewed_job", value=str(job_id))
    return {"job_id": job_id, "your_user_agent": user_agent}