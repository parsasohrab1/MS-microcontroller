"""
User Management Service
سرویس مدیریت کاربران - احراز هویت و مجوزدهی
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import os
from loguru import logger

from .database import get_db, engine, Base
from .models import User, UserRole
from .routers import auth, users

# تنظیمات
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ایجاد جداول
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="User Management Service",
    description="سرویس مدیریت کاربران و احراز هویت",
    version="1.0.0"
)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "User Management Service",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected"  # TODO: بررسی اتصال به پایگاه داده
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

