"""
Audit Logging
ثبت تمام دسترسی‌ها به داده‌ها و تغییرات تنظیمات
"""

from typing import Optional, Dict, List
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from loguru import logger
import json

Base = declarative_base()


# ============================================================================
# Audit Event Types
# ============================================================================

class AuditEventType(str, Enum):
    """انواع رویدادهای audit"""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"
    
    # Data Access
    VIEW_PATIENT_DATA = "view_patient_data"
    VIEW_TREATMENT = "view_treatment"
    VIEW_SETTINGS = "view_settings"
    
    # Data Modification
    CREATE_PATIENT = "create_patient"
    UPDATE_PATIENT = "update_patient"
    DELETE_PATIENT = "delete_patient"
    CREATE_TREATMENT = "create_treatment"
    UPDATE_TREATMENT = "update_treatment"
    DELETE_TREATMENT = "delete_treatment"
    
    # Settings
    UPDATE_SETTINGS = "update_settings"
    UPDATE_USER_ROLE = "update_user_role"
    
    # System
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONFIG_CHANGE = "config_change"


# ============================================================================
# Audit Log Model
# ============================================================================

class AuditLog(Base):
    """مدل Audit Log"""
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    event_type = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    user_email = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    resource_type = Column(String, nullable=True)  # patient, treatment, etc.
    resource_id = Column(String, nullable=True)
    action = Column(String, nullable=True)  # create, update, delete, view
    details = Column(JSON, nullable=True)  # Additional details
    success = Column(String, nullable=True, default="true")  # true/false
    error_message = Column(Text, nullable=True)


# ============================================================================
# Audit Logger
# ============================================================================

class AuditLogger:
    """Logger برای audit events"""
    
    def __init__(self, db_session=None):
        """
        مقداردهی اولیه
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        ثبت رویداد audit
        
        Args:
            event_type: نوع رویداد
            user_id: شناسه کاربر
            user_email: ایمیل کاربر
            ip_address: آدرس IP
            user_agent: User agent
            resource_type: نوع منبع
            resource_id: شناسه منبع
            action: عمل انجام شده
            details: جزئیات اضافی
            success: موفقیت
            error_message: پیام خطا
        """
        try:
            audit_log = AuditLog(
                id=f"{datetime.utcnow().isoformat()}_{event_type.value}",
                timestamp=datetime.utcnow(),
                event_type=event_type.value,
                user_id=user_id,
                user_email=user_email,
                ip_address=ip_address,
                user_agent=user_agent,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                details=details or {},
                success="true" if success else "false",
                error_message=error_message
            )
            
            # ذخیره در database
            if self.db:
                self.db.add(audit_log)
                self.db.commit()
            
            # Log به file
            logger.info(
                f"Audit: {event_type.value} | "
                f"User: {user_id} ({user_email}) | "
                f"Resource: {resource_type}/{resource_id} | "
                f"Action: {action} | "
                f"Success: {success}"
            )
        
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
    
    def log_data_access(
        self,
        user_id: str,
        user_email: str,
        resource_type: str,
        resource_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        ثبت دسترسی به داده
        
        Args:
            user_id: شناسه کاربر
            user_email: ایمیل کاربر
            resource_type: نوع منبع
            resource_id: شناسه منبع
            ip_address: آدرس IP
            user_agent: User agent
        """
        event_type = AuditEventType.VIEW_PATIENT_DATA
        if resource_type == "treatment":
            event_type = AuditEventType.VIEW_TREATMENT
        elif resource_type == "settings":
            event_type = AuditEventType.VIEW_SETTINGS
        
        self.log_event(
            event_type=event_type,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action="view"
        )
    
    def log_data_modification(
        self,
        user_id: str,
        user_email: str,
        resource_type: str,
        resource_id: str,
        action: str,
        old_data: Optional[Dict] = None,
        new_data: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        ثبت تغییرات داده
        
        Args:
            user_id: شناسه کاربر
            user_email: ایمیل کاربر
            resource_type: نوع منبع
            resource_id: شناسه منبع
            action: عمل (create, update, delete)
            old_data: داده قدیمی
            new_data: داده جدید
            ip_address: آدرس IP
            user_agent: User agent
        """
        event_type_map = {
            "patient": {
                "create": AuditEventType.CREATE_PATIENT,
                "update": AuditEventType.UPDATE_PATIENT,
                "delete": AuditEventType.DELETE_PATIENT
            },
            "treatment": {
                "create": AuditEventType.CREATE_TREATMENT,
                "update": AuditEventType.UPDATE_TREATMENT,
                "delete": AuditEventType.DELETE_TREATMENT
            }
        }
        
        event_type = event_type_map.get(resource_type, {}).get(action)
        if not event_type:
            event_type = AuditEventType.UPDATE_SETTINGS
        
        details = {}
        if old_data:
            details["old_data"] = old_data
        if new_data:
            details["new_data"] = new_data
        
        self.log_event(
            event_type=event_type,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details
        )
    
    def log_authentication(
        self,
        user_id: Optional[str],
        user_email: Optional[str],
        event_type: AuditEventType,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        ثبت رویدادهای احراز هویت
        
        Args:
            user_id: شناسه کاربر
            user_email: ایمیل کاربر
            event_type: نوع رویداد
            ip_address: آدرس IP
            user_agent: User agent
            success: موفقیت
            error_message: پیام خطا
        """
        self.log_event(
            event_type=event_type,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
    
    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        دریافت audit logs
        
        Args:
            user_id: فیلتر بر اساس user_id
            event_type: فیلتر بر اساس event_type
            resource_type: فیلتر بر اساس resource_type
            resource_id: فیلتر بر اساس resource_id
            start_date: تاریخ شروع
            end_date: تاریخ پایان
            limit: حداکثر تعداد
        
        Returns:
            لیست audit logs
        """
        if not self.db:
            return []
        
        query = self.db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if event_type:
            query = query.filter(AuditLog.event_type == event_type.value)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        query = query.order_by(AuditLog.timestamp.desc())
        query = query.limit(limit)
        
        return query.all()


# Singleton instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(db_session=None) -> AuditLogger:
    """دریافت instance audit logger"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(db_session)
    return _audit_logger

