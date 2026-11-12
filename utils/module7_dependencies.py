from fastapi import Header, HTTPException, status, Query, Depends, Request
from models.orm import User
from utils.dependencies import get_current_user


# def demo_api_key(demo_api_key: str | None = Header(default=None)):
#     if demo_api_key != "demo-key":
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
#                             detail="Invalid API key")

#     return True


# class Demoapikey:
#     def __init__(self, expected_key: str):
#         self.expected_key = expected_key

#     def __call__(self, demo_api_key: str | None = Header(default=None)):
#         if demo_api_key != self.expected_key:
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
#                                 detail="Invalid API key")
#         return True


def pagniation(skip: int = Query(default=0, ge=0), limit: int = Query(default=10, ge=1, le=100)):
    return {"skip": skip, "limit": limit}


def get_candidate_context(current_user: User = Depends(get_current_user)):
    if current_user.role != "candidate":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only candidate can access this resourse")
    return current_user


class Pagination:
    def __init__(self, skip: int = Query(default=0, ge=0), limit: int = Query(default=10, ge=1, le=100)):
        self.skip = skip
        self.limit = limit


# def track_request(request: Request):
#     return (f"Request received: {request.method} {request.url.path}")
