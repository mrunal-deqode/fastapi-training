
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db
from routers import applications, jobs, auth, candidates, super_admin, module8_practice
# from models.orm import User
from middleware import logging_middleware
from fastapi.middleware.cors import CORSMiddleware
from utils.email_service import send_email

app = FastAPI(title="Recruitment & Hiring")

app.add_middleware(CORSMiddleware, allow_origins=[
                   "http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.middleware("http")(logging_middleware)


app.include_router(applications.router)
app.include_router(jobs.router)
app.include_router(auth.router)
app.include_router(candidates.router)
app.include_router(super_admin.router)
# app.include_router(module7_practice.router)
app.include_router(module8_practice.router)

# demo_key = Demoapikey(expected_key="demo_key")


@app.get("/")
def read_root():
    return {"message": "Recruitment & Hiring API is running"}


@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not reachable",
        )

    return {"database": "Connected"}


# @app.get("/test-dependency", tags=["Test Dependency"])
# def test_dependency(key: bool = Depends(demo_api_key)):
#     return {"message": "Dependecy executed succesfully", "Key": key}


# @app.get("/test-class-dependency", tags=["Test Dependency"])
# def test_class_dependency(key: bool = Depends(demo_key)):
#     return {"message": "Dependecy executed succesfully", "Key": key}


# @app.get("/candidate-context", tags=["Test Dependency"])
# def candidate_context(current_user: User = Depends(get_candidate_context)):
#     return {"message": "Candidate conetxt loaded successfully", "candidate_id": current_user.id, "role": current_user.role}

# @app.post("/test-email")
# def test_email(bg_task: BackgroundTasks, recipient: str):
#     bg_task.add_task(send_email, recipient, "Recruitment System - Email Test",
#                      "Hello! Your Gmail SMTP integration is working successfully.")

#     return {"message": "Email Scheduled successfully"}
