
from fastapi import APIRouter

from routers import applications, auth, candidates, jobs, module8_practice, super_admin

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth.router)
api_v1_router.include_router(jobs.router)
api_v1_router.include_router(applications.router)
api_v1_router.include_router(candidates.router)
api_v1_router.include_router(super_admin.router)
api_v1_router.include_router(module8_practice.router)
