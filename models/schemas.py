
from typing import Literal

from pydantic import BaseModel, Field


ApplicationStatus = Literal[
    "Applied",
    "Under Review",
    "Shortlisted",
    "Selected",
    "Rejected",
]


class ContactInfo(BaseModel):
    email: str = Field(
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )
    phone: str | None = Field(
        default=None, min_length=10, max_length=10
    )


class ApplicationCreate(BaseModel):
    candidate_name: str = Field(min_length=2, max_length=30)
    job_title: str = Field(min_length=2, max_length=100)
    contact: ContactInfo
    years_of_experience: int = Field(ge=0)


class ApplicationResponse(BaseModel):
    id: int
    candidate_name: str
    job_title: str
    contact: ContactInfo | None = None
    years_of_experience: int | None = None
    status: ApplicationStatus


class ApplicationUpdate(BaseModel):
    candidate_name: str | None = Field(
        default=None, min_length=2, max_length=30
    )
    job_title: str | None = None
    contact: ContactInfo | None = None
    years_of_experience: int | None = Field(default=None, ge=0)


class StatusUpdate(BaseModel):
    status: ApplicationStatus


class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=10)
    job_type: str
    deadline: str

    location: str = Field(min_length=2, max_length=100)
    min_experience_years: int = Field(default=0, ge=0)
    max_experience_years: int | None = Field(default=None, ge=0)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)


class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    job_type: str
    deadline: str
    location: str
    min_experience_years: int
    max_experience_years: int | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    status: Literal["open", "closed"]
    is_active: bool
