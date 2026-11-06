from fastapi import APIRouter, Depends, HTTPException, status
from models.schemas import CandidateRegister, CandidateResponse, TokenResponse
from sqlalchemy.orm import Session
from database import get_db
from models.orm import User
from utils.security import hash_password, verify_password

from fastapi.security import OAuth2PasswordRequestForm
from utils.jwt import create_access_token, create_refresh_token
from utils.dependencies import get_current_user


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
