from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.domain import UserProfile

router = APIRouter()

class UserProfileUpdate(BaseModel):
    name: str
    email: str
    role: str
    employee_id: str
    photo_url: str

@router.get("/profile")
def get_user_profile(db: Session = Depends(get_db)):
    profile = db.query(UserProfile).first()
    if not profile:
        # Create a default profile if none exists
        profile = UserProfile()
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return {
        "id": profile.id,
        "name": profile.name,
        "email": profile.email,
        "role": profile.role,
        "employee_id": profile.employee_id,
        "photo_url": profile.photo_url,
    }

@router.put("/profile")
def update_user_profile(profile_update: UserProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).first()
    if not profile:
        profile = UserProfile()
        db.add(profile)
    
    profile.name = profile_update.name
    profile.email = profile_update.email
    profile.role = profile_update.role
    profile.employee_id = profile_update.employee_id
    profile.photo_url = profile_update.photo_url
    
    db.commit()
    db.refresh(profile)
    return {
        "id": profile.id,
        "name": profile.name,
        "email": profile.email,
        "role": profile.role,
        "employee_id": profile.employee_id,
        "photo_url": profile.photo_url,
    }
