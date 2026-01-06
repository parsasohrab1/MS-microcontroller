"""
API v2 Routers
"""

from fastapi import APIRouter

# ایجاد router برای v2
v2_router = APIRouter(prefix="/api/v2", tags=["v2"])

# Import routers
# from .users import router as users_router
# v2_router.include_router(users_router)

