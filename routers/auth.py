from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models.orm import RevokedToken, User
from models.schemas import (
    CandidateRegister,
    CandidateResponse,
    RefreshTokenRequest,
    TokenResponse,
)
from redis_client import redis_client
from utils.dependencies import get_current_user, oauth2_scheme
from utils.jwt import create_access_token, create_refresh_token, verify_token
from utils.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new candidate",
    description=(
        "Creates a new candidate account using the supplied personal details. "
        "The password is securely hashed before storage. "
        "Email addresses must be unique."
    ),
    responses={
        201: {
            "description": "Candidate account created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 10,
                        "full_name": "Rahul Sharma",
                        "email": "rahul@example.com",
                        "phone": "9876543210",
                        "role": "candidate",
                        "is_active": True
                    }
                }
            }
        },
        409: {
            "description": "Email is already registered",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email is already registered."
                    }
                }
            }
        },
        422: {"description": "Invalid registration data"}
    }
)
def register_candidate(data: CandidateRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == data.email).first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Email is already registered.")

    new_candidate = User(
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(data.password),
        phone=data.phone,
        role="candidate",
        is_active=True
    )

    db.add(new_candidate)
    db.commit()
    db.refresh(new_candidate)

    return new_candidate


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate a user and generate tokens",
    description=(
        "Authenticates a user using email and password submitted as OAuth2 form data. "
        "Returns access and refresh JWT tokens after successful authentication. "
        "Login attempts are rate-limited by client IP. Five failed attempts "
        "trigger a temporary 60-second restriction."
    ),
    responses={
        200: {
            "description": "Authentication successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "example.access.token",
                        "refresh_token": "example.refresh.token",
                        "token_type": "bearer",
                        "role": "candidate"
                    }
                }
            }
        },
        401: {
            "description": "Invalid email or password"
        },
        403: {
            "description": "User account is inactive"
        },
        429: {
            "description": "Too many login attempts"
        },
        422: {
            "description": "Invalid login form data"
        }
    }
)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):

        client_ip = request.client.host
        key = f"rate_limit:login:{client_ip}"

        attempts = redis_client.incr(key)

        if attempts == 1:
            redis_client.expire(key, 60)

        if attempts >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts. Please try again after 60 seconds.")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Email or Password")

    client_ip = request.client.host
    key = f"rate_limit:login:{client_ip}"

    redis_client.delete(key)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is Inactive")

    token_data = {
        "sub": str(user.id),
        "role": user.role
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role
    }


@router.get(
    "/me",
    response_model=CandidateResponse,
    summary="Get current user profile",
    description=(
        "Returns the profile of the currently authenticated user. "
        "Requires a valid access token in the Authorization header."
    ),
    responses={
        200: {
            "description": "Current user profile retrieved",
            "content": {
                "application/json": {
                    "example": {
                        "id": 10,
                        "full_name": "Rahul Sharma",
                        "email": "rahul@example.com",
                        "phone": "9876543210",
                        "role": "candidate",
                        "is_active": True
                    }
                }
            }
        },
        401: {"description": "Missing or invalid access token"},
        403: {"description": "Access forbidden"}
    }
)
def get_my_account(current_user: User = Depends(get_current_user)):
    # print("current_user is :- ", current_user)
    return current_user


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh authentication tokens",
    description=(
        "Accepts a valid refresh token and issues a new access token "
        "and refresh token. The previous refresh token is revoked to "
        "prevent reuse. Revoked, expired, or invalid tokens are rejected."
    ),
    responses={
        200: {
            "description": "New authentication tokens generated",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "new.access.token",
                        "refresh_token": "new.refresh.token",
                        "token_type": "bearer",
                        "role": "candidate"
                    }
                }
            }
        },
        401: {
            "description": "Invalid, expired, or revoked refresh token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid or revoked refresh token"
                    }
                }
            }
        },
        422: {"description": "Invalid refresh token request"}
    }
)
def refresh_access_token(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or revoked refresh token"
    )

    payload = verify_token(data.refresh_token)

    if payload.get("type") != "refresh":
        raise credentials_exception

    jti = payload.get("jti")
    user_id = payload.get("sub")

    if not jti or not user_id or not user_id.isdigit():
        raise credentials_exception

    revoked_token = db.query(RevokedToken).filter(
        RevokedToken.jti == jti
    ).first()

    if revoked_token:
        raise credentials_exception

    user = db.query(User).filter(
        User.id == int(user_id),
        User.is_active.is_(True)
    ).first()

    if not user:
        raise credentials_exception

    db.add(
        RevokedToken(
            jti=jti,
            expires_at=datetime.fromtimestamp(
                payload["exp"],
                tz=timezone.utc
            )
        )
    )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise credentials_exception

    token_data = {
        "sub": str(user.id),
        "role": user.role
    }

    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
        "role": user.role
    }


@router.post(
    "/logout",
    summary="Logout the authenticated user",
    description=(
        "Logs out the currently authenticated user by revoking both "
        "the access token and refresh token. Requires a valid access "
        "token in the Authorization header and a refresh token in the request body."
    ),
    responses={
        200: {
            "description": "User logged out successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Logged out successfully"
                    }
                }
            }
        },
        401: {
            "description": "Invalid, expired, or already revoked token"
        },
        422: {
            "description": "Invalid refresh token request"
        }
    }
)
def logout(
    data: RefreshTokenRequest,
    access_token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
    )

    access_payload = verify_token(access_token)

    if (
        access_payload.get("type") != "access"
        or access_payload.get("sub") != str(current_user.id)
    ):
        raise credentials_exception

    refresh_payload = verify_token(data.refresh_token)

    if (
        refresh_payload.get("type") != "refresh"
        or refresh_payload.get("sub") != str(current_user.id)
    ):
        raise credentials_exception

    access_jti = access_payload["jti"]
    refresh_jti = refresh_payload["jti"]

    existing_refresh = db.query(RevokedToken).filter(
        RevokedToken.jti == refresh_jti
    ).first()

    if existing_refresh:
        raise credentials_exception

    db.add_all([
        RevokedToken(
            jti=access_jti,
            expires_at=datetime.fromtimestamp(
                access_payload["exp"],
                tz=timezone.utc
            )
        ),
        RevokedToken(
            jti=refresh_jti,
            expires_at=datetime.fromtimestamp(
                refresh_payload["exp"],
                tz=timezone.utc
            )
        )
    ])

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise credentials_exception

    return {
        "message": "Logged out successfully"
    }
