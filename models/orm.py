
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="candidate")
    full_name: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(10))
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    profile: Mapped["CandidateProfile | None"] = relationship(
        back_populates="user", uselist=False
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="candidate"
    )
    jobs_posted: Mapped[list["Job"]] = relationship(
        back_populates="creator"
    )


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True
    )
    address: Mapped[str | None] = mapped_column(String(255))
    education: Mapped[str | None] = mapped_column(Text)
    experience: Mapped[str | None] = mapped_column(Text)
    skills: Mapped[str | None] = mapped_column(Text)
    resume_url: Mapped[str | None] = mapped_column(String(500))

    user: Mapped["User"] = relationship(back_populates="profile")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    job_type: Mapped[str] = mapped_column(String(30))
    deadline: Mapped[date] = mapped_column(Date)

    location: Mapped[str] = mapped_column(
        String(100), default="Not specified",
        server_default="Not specified"
    )
    min_experience_years: Mapped[int] = mapped_column(
        default=0, server_default=text("0")
    )
    max_experience_years: Mapped[int | None] = mapped_column()
    salary_min: Mapped[int | None] = mapped_column()
    salary_max: Mapped[int | None] = mapped_column()

    status: Mapped[str] = mapped_column(
        String(20), default="open", server_default="open"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true")
    )

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    creator: Mapped["User"] = relationship(back_populates="jobs_posted")
    applications: Mapped[list["Application"]] = relationship(
        back_populates="job"
    )


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))

    years_of_experience: Mapped[int]
    cover_letter: Mapped[str | None] = mapped_column(Text)
    internal_notes: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(
        String(30), default="Applied", server_default="Applied"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    candidate: Mapped["User"] = relationship(
        back_populates="applications"
    )
    job: Mapped["Job"] = relationship(back_populates="applications")
