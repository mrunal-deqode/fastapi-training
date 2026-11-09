from fastapi import APIRouter, Depends, HTTPException, status
from models.schemas import CandidateRegister, CandidateResponse, RefreshTokenRequest, TokenResponse
from sqlalchemy.orm import Session
from database import get_db
from models.orm import RevokedToken, User
from utils.security import hash_password, verify_password

from fastapi.security import OAuth2PasswordRequestForm
from utils.jwt import create_access_token, create_refresh_token, verify_token
from utils.dependencies import get_current_user, oauth2_scheme

from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
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


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Email or Password")

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


@router.get("/me", response_model=CandidateResponse)
def get_my_account(current_user: User = Depends(get_current_user)):
    # print("current_user is :- ", current_user)
    return current_user


@router.post("/refresh", response_model=TokenResponse)
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


@router.post("/logout")
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
