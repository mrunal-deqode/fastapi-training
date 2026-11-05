from fastapi import APIRouter, Depends, HTTPException, status
from models.schemas import CandidateLogin, CandidateRegister, CandidateResponse
from sqlalchemy.orm import Session
from database import get_db
from models.orm import User
from utils.security import hash_password, verify_password


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


@router.post("/login", response_model=CandidateResponse)
def login_candidate(data: CandidateLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Email or Password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Your Account is deactivated, Please contact admin Admin@gmail.com")

    return user


@router.post("/admin/login", response_model=CandidateResponse)
def login_admin(data: CandidateLogin, db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.email == data.email,
                                  User.role == "admin").first()

    if not admin or not verify_password(data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Email or Password")

    if not admin.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Account is Deactivated")

    return admin


@router.post("/super-admin/login", response_model=CandidateResponse)
def login_super_admin(data: CandidateLogin, db: Session = Depends(get_db)):
    super_admin = db.query(User).filter(
        User.email == data.email,
        User.role == "super_admin",
    ).first()

    if not super_admin or not verify_password(data.password, super_admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")

    if not super_admin.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="User Acount is Deactivated")

    return super_admin
