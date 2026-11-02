from fastapi import APIRouter, status, Depends, HTTPException
from models.schemas import CandidateProfileCreate, CandidateProfileResponse, CandidateProfileUpdate
from database import get_db
import routers
from sqlalchemy.orm import Session
from models.orm import CandidateProfile, User

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.post("/profile", response_model=CandidateProfileResponse, status_code=status.HTTP_201_CREATED)
def create_candidate_profile(user_id:int, data:CandidateProfileCreate, db:Session=Depends(get_db)):
    candidate = db.query(User).filter(
        User.id == user_id,
        User.role == "candidate",
        User.is_active.is_(True)
    ).first()
    
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")
    
    existing_profile= db.query(CandidateProfile).filter(
        CandidateProfile.user_id == user_id
    ).first()
    
    if existing_profile:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Candidate Profile already exist")
    
    new_profile = CandidateProfile(
        user_id= user_id,
        address = data.address,
        education = data.education,
        experience= data.experience,
        skills= data.skills,
        resume_url=data.resume_url
    )
    
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    return new_profile


@router.get("/profile",response_model=CandidateProfileResponse)
def get_candidate_profile(user_id:int, db:Session = Depends(get_db)):
    candidate = db.query(User).filter(
        User.id == user_id,
        User.role == "candidate",
        User.is_active.is_(True)
    ).first()
    
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Details Not Found")
    
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Profile Not Found")
    
    return profile

@router.put("/profile", response_model=CandidateProfileResponse)
def update_candidate_full_profile(user_id:int, data:CandidateProfileCreate, db:Session =Depends(get_db)):
    candidate = db.query(User).filter(
        User.id == user_id,
        User.role == "candidate",
        User.is_active.is_(True)
    ).first()
    
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Details Not Found")
    
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
        
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Profile Not Found")
    
    profile.education = data.education
    profile.experience = data.experience
    profile.address = data.address
    profile.skills = data.skills
    profile.resume_url = data.resume_url
    
    db.commit()
    db.refresh(profile)
    
    return profile


@router.patch("/profile", response_model=CandidateProfileResponse)
def update_candidate_profile(user_id:int, data:CandidateProfileUpdate, db:Session=Depends(get_db)):
    candidate = db.query(User).filter(
            User.id == user_id,
            User.role == "candidate",
            User.is_active.is_(True)
        ).first()
        
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Details Not Found")
        
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
            
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Profile Not Found")
    
    changes = data.model_dump(exclude_unset=True)
    
    if not changes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No Data Provided to Update")
    
    for field, value in changes.items():
        setattr(profile,field,value)
        
    db.commit()
    db.refresh(profile)
    
    return profile