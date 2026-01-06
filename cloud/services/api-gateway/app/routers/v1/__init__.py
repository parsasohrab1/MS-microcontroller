"""
API v1 Routers
"""

from fastapi import APIRouter

# ایجاد router برای v1
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

# Import routers
# from .users import router as users_router
# from .data import router as data_router
# v1_router.include_router(users_router)
# v1_router.include_router(data_router)

