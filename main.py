
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db
from routers import applications, jobs


app = FastAPI(title="Recruitment & Hiring")


app.include_router(applications.router)
app.include_router(jobs.router)


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
