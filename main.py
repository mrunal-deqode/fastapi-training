
import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from logging_config import setup_logging

# from models.orm import User
from middleware import logging_middleware
from redis_client import redis_client

# from routers import applications, auth, candidates, jobs, module8_practice, super_admin
from routers.api_v1 import api_v1_router

setup_logging()

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
    )

app = FastAPI(title="Recruitment & Hiring")
app.middleware("http")(logging_middleware)

app.add_middleware(CORSMiddleware, allow_origins=[
                   "http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# app.include_router(applications.router)
# app.include_router(jobs.router)
# app.include_router(auth.router)
# app.include_router(candidates.router)
# app.include_router(super_admin.router)
# app.include_router(module7_practice.router)
# app.include_router(module8_practice.router)

app.include_router(api_v1_router)

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

@app.get("/health")
def health_check():
    return {"status": "healthy"}


# @app.get("/sentry-debug")
# def sentry_debug():
#     raise RuntimeError("Module 12 Sentry test exception")

@app.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    database_status = "connected"
    redis_status = "connected"

    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        database_status = "unavailable"

    try:
        redis_client.ping()
    except RedisError:
        redis_status = "unavailable"

    if database_status == "unavailable" or redis_status == "unavailable":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database": database_status,
                "redis": redis_status,
            },
        )

    return {
        "status": "ready",
        "database": database_status,
        "redis": redis_status,
    }


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
