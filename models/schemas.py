
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


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
    candidate_id: int = Field(gt=0)
    job_id: int = Field(gt=0)
    years_of_experience: int = Field(ge=0)
    cover_letter: str | None = None

class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    candidate_id: int
    job_id: int
    years_of_experience: int
    cover_letter: str | None = None
    status: ApplicationStatus
    is_active: bool

class ApplicationUpdate(BaseModel):
    years_of_experience: int | None = Field(
        default=None, ge=0
    )
    cover_letter: str | None = None

class ApplicationReplace(BaseModel):
    candidate_id: int = Field(gt=0)
    job_id: int = Field(gt=0)
    years_of_experience: int = Field(ge=0)
    cover_letter: str | None = None

class StatusUpdate(BaseModel):
    status: ApplicationStatus

class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=10)
    job_type: str
    deadline: date
    location: str = Field(min_length=2, max_length=100)
    min_experience_years: int = Field(default=0, ge=0)
    max_experience_years: int | None = Field(default=None, ge=0)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: str
    job_type: str
    deadline: date
    location: str
    min_experience_years: int
    max_experience_years: int | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    status: Literal["open", "closed"]
    is_active: bool
