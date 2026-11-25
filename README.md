# Recruitment & Hiring Management System

A FastAPI-based recruitment platform for managing job openings, candidate profiles, applications, and recruitment workflows within a single organization.

## Features

### Candidate

- Register and log in.
- Create and maintain a reusable candidate profile.
- Browse and filter job openings.
- Apply for jobs and track application status.
- View a personalized dashboard.

### Admin / Recruiter

- Create and manage job openings.
- View applicants for jobs created by the admin.
- Filter applicants by application status.
- View candidate and application details.
- Update application status.
- Access an admin dashboard.

### Super Admin

- Create and manage admin accounts.
- View and deactivate candidate accounts.
- Manage jobs across the organization.
- Deactivate and reactivate accounts and jobs.

### Platform capabilities

- JWT-based authentication with access and refresh tokens.
- Role-based authorization and resource ownership checks.
- PostgreSQL persistence with SQLAlchemy.
- Alembic database migrations.
- Redis caching for job listings and dashboards.
- Celery background processing for application status email notifications.
- Request ID logging and Prometheus metrics.
- Sentry error monitoring when configured.
- Docker Compose deployment.
- Pytest test suite and Locust load testing.

## Technology Stack

| Component          | Technology                 |
| ------------------ | -------------------------- |
| API                | FastAPI                    |
| Language           | Python 3.11                |
| Database           | PostgreSQL 16              |
| ORM                | SQLAlchemy 2.x             |
| Validation         | Pydantic                   |
| Migrations         | Alembic                    |
| Authentication     | JWT                        |
| Cache / Broker     | Redis                      |
| Background jobs    | Celery                     |
| Application server | Gunicorn + Uvicorn workers |
| Logging            | Structured JSON logging    |
| Metrics            | Prometheus                 |
| Error monitoring   | Sentry                     |
| Testing            | Pytest                     |
| Load testing       | Locust                     |
| Deployment         | Docker Compose             |

## Data Model

The main database entities are:

- **User** — stores account email, password hash, role, profile information, and account status.
- **CandidateProfile** — stores reusable candidate information such as education, experience, skills, address, and resume URL.
- **Job** — stores job descriptions, type, deadline, location, experience requirements, salary range, status, and creator.
- **Application** — connects a candidate to a job and stores experience, cover letter, internal notes, application status, and active status.
- **RevokedToken** — stores revoked JWT identifiers.
- **IdempotencyRecord** — records idempotency keys and responses to support safe application request retries.

### Relationships

- A User can create multiple Jobs.
- A User can have one CandidateProfile.
- A Candidate can submit applications to multiple Jobs.
- A Job can receive applications from multiple Candidates.
- A candidate can apply only once to a particular job.

## Role-Based Access Control

| Capability                     | Candidate |     Admin     | Super Admin |
| ------------------------------ | :-------: | :-----------: | :---------: |
| Manage own profile             |    Yes    |      No       |     No      |
| Browse jobs                    |    Yes    |      Yes      |     Yes     |
| Apply for jobs                 |    Yes    |      No       |     No      |
| View own applications          |    Yes    |      No       |     No      |
| Create jobs                    |    No     |      Yes      |     Yes     |
| Manage jobs created by self    |    No     |      Yes      |     No      |
| View applicants for owned jobs |    No     |      Yes      |     Yes     |
| Update application status      |    No     | Yes, own jobs |     Yes     |
| Manage admin accounts          |    No     |      No       |     Yes     |
| Manage candidates              |    No     |      No       |     Yes     |
| Manage all jobs                |    No     |      No       |     Yes     |

Access to another user's resources is restricted through authorization and ownership checks. Deactivated accounts cannot access the system.

## API Reference

All business API routes are mounted under `/api/v1`.

Interactive API documentation is available at `/docs` when the application is running.

### Authentication — `/api/v1/auth`

| Method | Endpoint    | Description                    |
| ------ | ----------- | ------------------------------ |
| POST   | `/register` | Register a candidate           |
| POST   | `/login`    | Authenticate and obtain tokens |
| GET    | `/me`       | Get current account            |
| POST   | `/refresh`  | Refresh access token           |
| POST   | `/logout`   | Log out and revoke token       |

### Jobs — `/api/v1/jobs`

| Method | Endpoint         | Description                    |
| ------ | ---------------- | ------------------------------ |
| GET    | `/`              | List available jobs            |
| GET    | `/manage`        | List jobs for administration   |
| GET    | `/{job_id}`      | Get job details                |
| POST   | `/`              | Create a job                   |
| GET    | `/{job_id}/info` | Get additional job information |

### Applications — `/api/v1/applications`

| Method | Endpoint                                      | Description                           |
| ------ | --------------------------------------------- | ------------------------------------- |
| POST   | `/`                                           | Submit an application                 |
| GET    | `/`                                           | List applications                     |
| GET    | `/my-applications`                            | List current candidate's applications |
| GET    | `/{application_id}`                           | Get application details               |
| PUT    | `/{application_id}`                           | Replace application fields            |
| PATCH  | `/{application_id}`                           | Partially update an application       |
| DELETE | `/{application_id}`                           | Deactivate an application             |
| GET    | `/admin/jobs/{job_id}/appliactions`           | List applicants for an admin's job    |
| GET    | `/admin/applications/{application_id}`        | Get applicant details                 |
| PATCH  | `/admin/applications/{application_id}/status` | Update application status             |

### Candidate Profiles — `/api/v1/candidates`

| Method | Endpoint   | Description                        |
| ------ | ---------- | ---------------------------------- |
| POST   | `/profile` | Create candidate profile           |
| GET    | `/profile` | Get candidate profile              |
| PUT    | `/profile` | Replace candidate profile          |
| PATCH  | `/profile` | Partially update candidate profile |

### Super Admin — `/api/v1/super-admin`

| Method | Endpoint                 | Description           |
| ------ | ------------------------ | --------------------- |
| POST   | `/create-admin`          | Create admin          |
| GET    | `/get-admins`            | List admins           |
| GET    | `/get-admin-details`     | Get admin details     |
| PATCH  | `/deactivate-admin`      | Deactivate admin      |
| PATCH  | `/reactivate-admin`      | Reactivate admin      |
| GET    | `/get-candidates`        | List candidates       |
| GET    | `/get-candidate-details` | Get candidate details |
| PATCH  | `/deactivate-candidate`  | Deactivate candidate  |
| PATCH  | `/reactivate-candidate`  | Reactivate candidate  |
| GET    | `/get-jobs`              | List all jobs         |
| GET    | `/get-job-detail`        | Get job details       |
| PUT    | `/update-job`            | Update a job          |
| PATCH  | `/update-status`         | Update job status     |

### Dashboards — `/api/v1/dashboard`

| Method | Endpoint     | Description         |
| ------ | ------------ | ------------------- |
| GET    | `/candidate` | Candidate dashboard |
| GET    | `/admin`     | Admin dashboard     |

### Operational Endpoints

These endpoints are outside the `/api/v1` prefix.

| Endpoint    | Description                                     |
| ----------- | ----------------------------------------------- |
| `/`         | Root API information                            |
| `/db-check` | Database connectivity check                     |
| `/health`   | Application health check                        |
| `/ready`    | Database and Redis readiness check              |
| `/metrics`  | Prometheus metrics; requires super-admin access |

## Getting Started

### Prerequisites

- Docker Engine
- Docker Compose plugin

For local development without Docker, also install Python 3.11 and PostgreSQL and Redis.

### 1. Clone the repository

```bash
git clone <repository-url>
cd FastAPI-Training
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Update `.env` with your own values. In particular, configure:

- PostgreSQL credentials.
- A strong JWT secret.
- SMTP email credentials.
- Redis connection URL.
- Locust test account credentials.
- Allowed CORS origins.

Do not commit `.env` or expose credentials in source control.

For Docker Compose, the database and Redis service hostnames are configured internally by Compose. Keep the Compose-compatible hostnames in the example configuration.

### 3. Start the application

```bash
docker compose up --build -d
```

Docker Compose starts PostgreSQL and Redis, runs Alembic migrations, and then starts the API and Celery worker. Locust is also included in the Compose stack.

### 4. Verify the application

- API: http://localhost:8000
- Swagger documentation: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Readiness: http://localhost:8000/ready
- Locust UI: http://localhost:8089

Check running containers and logs:

```bash
docker compose ps
docker compose logs -f app
docker compose logs -f worker
```

### 5. Stop the application

```bash
docker compose down
```

To also remove the PostgreSQL data volume:

```bash
docker compose down -v
```

**Warning:** The `-v` option deletes the database volume and its stored data.

## Database Migrations

Migrations are managed using Alembic.

Docker Compose runs:

```bash
alembic upgrade head
```

To create a migration during local development:

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

Review autogenerated migrations before applying them.

## Local Development

Create and activate a virtual environment:

```bash
python3.11 -m venv venv311
source venv311/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the required environment variables and start the API:

```bash
uvicorn main:app --reload
```

Start a Celery worker in another terminal:

```bash
celery -A celery_app.celery_app worker --loglevel=info
```

Ensure PostgreSQL and Redis are running and their URLs are configured correctly.

## Testing and Code Quality

Run the complete test suite:

```bash
python -m pytest -q
```

Run Ruff:

```bash
python -m ruff check .
```

Check patch formatting:

```bash
git diff --check
```

The test suite uses a dedicated test database configured through `TEST_DATABASE_URL`. Do not point tests at a production database.

## Background Jobs

Celery handles background application status email notifications. Redis is used as the message broker and for application caching.

The worker runs through Docker Compose or can be started manually using the command in the Local Development section.

## Load Testing

Locust is included in the Docker Compose configuration.

Open http://localhost:8089 after starting the stack. Configure the desired number of users and spawn rate in the Locust UI.

The load-test account is configured through `LOCUST_EMAIL` and `LOCUST_PASSWORD`.

Historical performance observations and limitations are documented in:

- `MODULE_15_PERFORMANCE_NOTES.md`
- `docs/module15-performance-notes.md`

## Project Structure

```text
.
├── alembic/              # Database migrations
├── docs/                 # Project documentation
├── models/
│   ├── orm.py             # SQLAlchemy models
│   └── schemas.py         # Pydantic schemas
├── routers/               # API route modules
├── scripts/               # Utility scripts
├── tests/                 # Automated tests
├── utils/                 # Authentication and shared utilities
├── celery_app.py          # Celery configuration
├── config.py              # Application settings
├── database.py            # Database configuration
├── docker-compose.yml     # Multi-service deployment
├── Dockerfile             # API and worker image
├── locustfile.py          # Load-testing scenarios
├── main.py                # FastAPI application entry point
├── middleware.py          # Request ID, logging, security headers, metrics
├── redis_client.py        # Redis client and cache helpers
└── tasks.py               # Background tasks
```

## Current Scope and Limitations

- Designed for one organization's recruitment process.
- No interview scheduling workflow.
- No application status history.
- No multi-company or tenant support.
- Application records are deactivated rather than permanently deleted.
- Performance observations are documented in the Module 15 notes; high-concurrency connection-pool improvements require further verification.

## Security Notes

- Never commit `.env` or real credentials.
- Use a strong, unique JWT secret in deployed environments.
- Configure CORS with trusted frontend origins only.
- Use HTTPS in production.
- Keep the test database separate from production.
- Review authorization checks whenever adding endpoints that access user-owned resources.

## License

Add the appropriate license information before public distribution.
