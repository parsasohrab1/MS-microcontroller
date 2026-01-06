"""
API Versioning
مدیریت نسخه‌های API
"""

from typing import Optional, Callable, Dict
from fastapi import APIRouter, Request, HTTPException
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from datetime import datetime
from loguru import logger
import re


class VersionedAPIRoute(APIRoute):
    """Route با پشتیبانی از versioning"""
    
    def __init__(self, *args, version: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.version = version


class APIVersionManager:
    """مدیریت نسخه‌های API"""
    
    def __init__(self):
        """مقداردهی اولیه"""
        self.supported_versions = ["v1", "v2", "v3"]
        self.default_version = "v1"
        self.deprecated_versions = []
        self.version_routers: dict = {}
    
    def register_version(self, version: str, router: APIRouter):
        """
        ثبت router برای نسخه مشخص
        
        Args:
            version: نسخه API (مثلاً "v1")
            router: FastAPI router
        """
        if version not in self.supported_versions:
            logger.warning(f"Unsupported version {version}, adding to supported versions")
            self.supported_versions.append(version)
        
        self.version_routers[version] = router
        logger.info(f"Registered API version {version}")
    
    def get_version_from_header(self, request: Request) -> str:
        """
        استخراج نسخه از header
        
        Args:
            request: FastAPI request
        
        Returns:
            نسخه API
        """
        # بررسی header
        accept_header = request.headers.get("Accept", "")
        
        # فرمت: application/vnd.api+json;version=v1
        version_match = re.search(r'version=([\w.]+)', accept_header)
        if version_match:
            version = version_match.group(1)
            if version in self.supported_versions:
                return version
        
        # بررسی query parameter
        version = request.query_params.get("version")
        if version and version in self.supported_versions:
            return version
        
        # بررسی path
        path = request.url.path
        version_match = re.search(r'/v(\d+)/', path)
        if version_match:
            version = f"v{version_match.group(1)}"
            if version in self.supported_versions:
                return version
        
        # پیش‌فرض
        return self.default_version
    
    def get_version_router(self, version: str) -> Optional[APIRouter]:
        """
        دریافت router برای نسخه مشخص
        
        Args:
            version: نسخه API
        
        Returns:
            Router یا None
        """
        return self.version_routers.get(version)
    
    def deprecate_version(self, version: str, sunset_date: Optional[str] = None):
        """
        Deprecate کردن نسخه
        
        Args:
            version: نسخه برای deprecate
            sunset_date: تاریخ sunset (ISO format)
        """
        if version not in self.deprecated_versions:
            self.deprecated_versions.append(version)
            logger.warning(f"Deprecated API version {version}, sunset: {sunset_date}")
    
    def check_deprecated(self, version: str) -> Optional[Dict]:
        """
        بررسی اینکه آیا نسخه deprecated است
        
        Args:
            version: نسخه API
        
        Returns:
            Dict با اطلاعات deprecation یا None
        """
        if version in self.deprecated_versions:
            return {
                "deprecated": True,
                "version": version,
                "message": f"API version {version} is deprecated",
                "sunset_date": None  # TODO: اضافه کردن sunset date
            }
        return None


# Singleton instance
_version_manager: Optional[APIVersionManager] = None


def get_version_manager() -> APIVersionManager:
    """دریافت instance version manager"""
    global _version_manager
    if _version_manager is None:
        _version_manager = APIVersionManager()
    return _version_manager


# Middleware برای versioning
async def version_middleware(request: Request, call_next: Callable):
    """Middleware برای مدیریت versioning"""
    version_manager = get_version_manager()
    
    # استخراج نسخه
    version = version_manager.get_version_from_header(request)
    
    # بررسی deprecation
    deprecation_info = version_manager.check_deprecated(version)
    if deprecation_info:
        # اضافه کردن warning header
        response = await call_next(request)
        response.headers["X-API-Deprecated"] = "true"
        response.headers["X-API-Version"] = version
        response.headers["Warning"] = f'299 - "{deprecation_info["message"]}"'
        return response
    
    # اضافه کردن version به request state
    request.state.api_version = version
    
    response = await call_next(request)
    response.headers["X-API-Version"] = version
    
    return response

