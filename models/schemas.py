from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict, EmailStr
# from test_security import password

ApplicationStatus = Literal[
    "Applied",
    "Under Review",
    "Shortlisted",
    "Selected",
    "Rejected",
]


class ApplicationCreate(BaseModel):
    candidate_id: int = Field(gt=0)
    job_id: int = Field(gt=0)
    years_of_experience: float = Field(ge=0)
    cover_letter: str | None = None


class CandidateApplicationCreate(BaseModel):
    job_id: int = Field(gt=0)
    years_of_experience: float = Field(ge=0)
    cover_letter: str | None = None


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    job_id: int
    years_of_experience: float
    cover_letter: str | None = None
    status: ApplicationStatus
    is_active: bool


class ApplicationUpdate(BaseModel):
    years_of_experience: float | None = Field(
        default=None, ge=0
    )
    cover_letter: str | None = None


class ApplicationReplace(BaseModel):
    candidate_id: int = Field(gt=0)
    job_id: int = Field(gt=0)
    years_of_experience: float = Field(ge=0)
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


class CandidateRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=6, max_length=100)
    phone: str | None = Field(default=None, pattern=r"^[0-9]{10}$")


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str | None
    email: EmailStr
    phone: str | None
    role: str
    is_active: bool


class CandidateLogin(BaseModel):
    email: EmailStr = Field(max_length=255)
    password: str


class CandidateProfileCreate(BaseModel):
    address: str | None = Field(default=None, max_length=255)
    education: str | None = None
    experience: str | None = None
    skills: str | None = None
    resume_url: str | None = Field(default=None, max_length=500)


class CandidateProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    address: str | None
    education: str | None
    experience: str | None
    skills: str | None
    resume_url: str | None


class CandidateProfileUpdate(BaseModel):
    address: str | None = Field(default=None, max_length=255)
    education: str | None = None
    experience: str | None = None
    skills: str | None = None
    resume_url: str | None = Field(default=None, max_length=500)


class ApplicantDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: int
    candidate_id: int
    candidate_name: str | None
    candidate_email: EmailStr
    candidate_phone: str | None
    years_of_experience: float
    cover_letter: str | None
    status: ApplicationStatus


class AdminApplicantDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: int
    job_id: int
    candidate_id: int
    candidate_name: str | None
    candidate_email: EmailStr
    candidate_phone: str | None

    years_of_experience: float
    cover_letter: str | None
    status: ApplicationStatus

    education: str | None
    experience: str | None
    skills: str | None
    resume_url: str | None


class AdminCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8)
    phone: str | None = Field(default=None, pattern=r"^\d{10}$")


class AdminCreateResopnse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str | None
    email: EmailStr
    phone: str | None
    role: str
    is_active: bool


class JobStatusUpdate(BaseModel):
    status: Literal["open", "closed"]


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
