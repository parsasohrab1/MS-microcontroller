"""
Role-Based Access Control (RBAC)
پیاده‌سازی RBAC برای مدیریت دسترسی‌ها
"""

from typing import List, Optional, Set, Dict
from enum import Enum
from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from loguru import logger
from datetime import datetime

from ..database import get_db
from ..models import User, UserRole
from .oauth2 import get_current_user, TokenData


# ============================================================================
# Roles
# ============================================================================

class Role(str, Enum):
    """نقش‌های سیستم"""
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    PATIENT = "patient"
    RESEARCHER = "researcher"


# ============================================================================
# Permissions
# ============================================================================

class Permission(str, Enum):
    """مجوزهای سیستم"""
    # Patient data
    VIEW_PATIENT_DATA = "view_patient_data"
    EDIT_PATIENT_DATA = "edit_patient_data"
    DELETE_PATIENT_DATA = "delete_patient_data"
    
    # Treatment
    VIEW_TREATMENT = "view_treatment"
    EDIT_TREATMENT = "edit_treatment"
    DELETE_TREATMENT = "delete_treatment"
    
    # Settings
    VIEW_SETTINGS = "view_settings"
    EDIT_SETTINGS = "edit_settings"
    
    # Users
    VIEW_USERS = "view_users"
    EDIT_USERS = "edit_users"
    DELETE_USERS = "delete_users"
    
    # Research
    VIEW_RESEARCH_DATA = "view_research_data"
    EXPORT_RESEARCH_DATA = "export_research_data"
    
    # System
    VIEW_SYSTEM_LOGS = "view_system_logs"
    MANAGE_SYSTEM = "manage_system"


# ============================================================================
# Role-Permission Mapping
# ============================================================================

ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.VIEW_PATIENT_DATA,
        Permission.EDIT_PATIENT_DATA,
        Permission.DELETE_PATIENT_DATA,
        Permission.VIEW_TREATMENT,
        Permission.EDIT_TREATMENT,
        Permission.DELETE_TREATMENT,
        Permission.VIEW_SETTINGS,
        Permission.EDIT_SETTINGS,
        Permission.VIEW_USERS,
        Permission.EDIT_USERS,
        Permission.DELETE_USERS,
        Permission.VIEW_RESEARCH_DATA,
        Permission.EXPORT_RESEARCH_DATA,
        Permission.VIEW_SYSTEM_LOGS,
        Permission.MANAGE_SYSTEM
    },
    Role.DOCTOR: {
        Permission.VIEW_PATIENT_DATA,
        Permission.EDIT_PATIENT_DATA,
        Permission.VIEW_TREATMENT,
        Permission.EDIT_TREATMENT,
        Permission.VIEW_SETTINGS,
        Permission.VIEW_RESEARCH_DATA
    },
    Role.NURSE: {
        Permission.VIEW_PATIENT_DATA,
        Permission.VIEW_TREATMENT,
        Permission.VIEW_SETTINGS
    },
    Role.PATIENT: {
        Permission.VIEW_PATIENT_DATA,  # فقط داده‌های خودش
        Permission.VIEW_TREATMENT  # فقط درمان خودش
    },
    Role.RESEARCHER: {
        Permission.VIEW_RESEARCH_DATA,  # فقط داده‌های anonymized
        Permission.EXPORT_RESEARCH_DATA
    }
}


# ============================================================================
# RBAC Manager
# ============================================================================

class RBACManager:
    """مدیریت RBAC"""
    
    @staticmethod
    def get_role_permissions(role: Role) -> Set[Permission]:
        """
        دریافت مجوزهای یک نقش
        
        Args:
            role: نقش
        
        Returns:
            مجموعه مجوزها
        """
        return ROLE_PERMISSIONS.get(role, set())
    
    @staticmethod
    def has_permission(role: Role, permission: Permission) -> bool:
        """
        بررسی اینکه آیا نقش مجوز دارد
        
        Args:
            role: نقش
            permission: مجوز
        
        Returns:
            True اگر مجوز دارد
        """
        permissions = RBACManager.get_role_permissions(role)
        return permission in permissions
    
    @staticmethod
    def check_permission(role: Role, permission: Permission) -> bool:
        """
        بررسی مجوز (با exception)
        
        Args:
            role: نقش
            permission: مجوز
        
        Returns:
            True اگر مجوز دارد
        
        Raises:
            HTTPException اگر مجوز ندارد
        """
        if not RBACManager.has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}"
            )
        return True
    
    @staticmethod
    def get_user_role(user_id: str, db) -> Optional[Role]:
        """
        دریافت نقش کاربر
        
        Args:
            user_id: شناسه کاربر
            db: Database session
        
        Returns:
            نقش کاربر یا None
        """
        # TODO: دریافت از database
        # user = db.query(User).filter(User.id == user_id).first()
        # if user:
        #     return Role(user.role)
        return None


# ============================================================================
# Dependencies
# ============================================================================

def require_role(*roles: Role):
    """
    Dependency برای بررسی نقش
    
    Args:
        *roles: نقش‌های مجاز
    
    Returns:
        Dependency function
    """
    async def role_checker(current_user: TokenData = Depends(get_current_user)):
        # TODO: دریافت نقش از database
        # user_role = RBACManager.get_user_role(current_user.user_id, db)
        # if user_role not in roles:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail=f"Role required: {', '.join([r.value for r in roles])}"
        #     )
        # return current_user
        return current_user
    
    return role_checker


def require_permission(permission: Permission):
    """
    Dependency برای بررسی مجوز
    
    Args:
        permission: مجوز مورد نیاز
    
    Returns:
        Dependency function
    """
    async def permission_checker(current_user: TokenData = Depends(get_current_user)):
        # TODO: دریافت نقش از database
        # user_role = RBACManager.get_user_role(current_user.user_id, db)
        # RBACManager.check_permission(user_role, permission)
        return current_user
    
    return permission_checker


# ============================================================================
# Helper Functions
# ============================================================================

def check_patient_access(user_id: str, patient_id: str, db) -> bool:
    """
    بررسی دسترسی به داده‌های patient
    
    Args:
        user_id: شناسه کاربر
        patient_id: شناسه patient
        db: Database session
    
    Returns:
        True اگر دسترسی دارد
    """
    # TODO: بررسی نقش کاربر
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     return False
    # 
    # role = Role(user.role)
    # 
    # # Admin و Doctor دسترسی کامل دارند
    # if role in [Role.ADMIN, Role.DOCTOR]:
    #     return True
    # 
    # # Patient فقط به داده‌های خودش دسترسی دارد
    # if role == Role.PATIENT:
    #     return user_id == patient_id
    # 
    # # Nurse دسترسی محدود دارد
    # if role == Role.NURSE:
    #     # TODO: بررسی assignment
    #     return True
    # 
    # return False
    return True


def check_research_data_access(user_id: str, db) -> bool:
    """
    بررسی دسترسی به داده‌های research
    
    Args:
        user_id: شناسه کاربر
        db: Database session
    
    Returns:
        True اگر دسترسی دارد
    """
    # TODO: بررسی نقش
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     return False
    # 
    # role = Role(user.role)
    # return role in [Role.ADMIN, Role.DOCTOR, Role.RESEARCHER]
    return True

