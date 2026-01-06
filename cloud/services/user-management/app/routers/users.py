"""
Users Router
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from ..database import get_db
from ..models import User, UserRole
from .auth import get_current_user as get_current_user_from_auth

router = APIRouter()


# Pydantic models
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: Optional[str]
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[str] = None


# Routes
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user_from_auth)
):
    """دریافت اطلاعات کاربر فعلی"""
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user_from_auth),
    db: Session = Depends(get_db)
):
    """دریافت اطلاعات یک کاربر"""
    # فقط کاربر خودش یا ادمین می‌تواند اطلاعات را ببیند
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user_from_auth),
    db: Session = Depends(get_db)
):
    """به‌روزرسانی اطلاعات کاربر"""
    # فقط کاربر خودش یا ادمین می‌تواند به‌روزرسانی کند
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # به‌روزرسانی فیلدها
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.phone_number is not None:
        user.phone_number = user_update.phone_number
    if user_update.date_of_birth is not None:
        # TODO: تبدیل string به datetime
        pass
    
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user_from_auth),
    db: Session = Depends(get_db)
):
    """حذف کاربر (غیرفعال کردن)"""
    # فقط ادمین می‌تواند کاربر را حذف کند
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # غیرفعال کردن به جای حذف
    user.is_active = False
    db.commit()
    
    return None

