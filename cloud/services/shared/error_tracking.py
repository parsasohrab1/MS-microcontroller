"""
Error Tracking with Sentry
پیاده‌سازی Error Tracking با Sentry
"""

import os
from typing import Optional, Dict, Any
from loguru import logger

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logger.warning("Sentry SDK not installed. Error tracking will be disabled.")


def init_sentry(
    dsn: Optional[str] = None,
    environment: str = "production",
    release: Optional[str] = None,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1
):
    """
    مقداردهی اولیه Sentry
    
    Args:
        dsn: Sentry DSN
        environment: محیط (staging, production)
        release: نسخه
        traces_sample_rate: نرخ نمونه‌برداری traces
        profiles_sample_rate: نرخ نمونه‌برداری profiles
    """
    if not SENTRY_AVAILABLE:
        logger.warning("Sentry SDK not available")
        return
    
    dsn = dsn or os.getenv("SENTRY_DSN")
    if not dsn:
        logger.warning("Sentry DSN not provided")
        return
    
    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            # Set user context
            before_send=before_send_filter,
        )
        logger.info("Sentry initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def before_send_filter(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter events before sending to Sentry
    
    Args:
        event: Event data
        hint: Hint data
    
    Returns:
        Filtered event or None
    """
    # Filter out sensitive data
    if 'request' in event:
        if 'data' in event['request']:
            # Remove sensitive fields
            sensitive_fields = ['password', 'token', 'secret', 'key']
            for field in sensitive_fields:
                if field in event['request']['data']:
                    event['request']['data'][field] = '[FILTERED]'
    
    return event


def capture_exception(error: Exception, context: Optional[Dict[str, Any]] = None):
    """
    Capture exception
    
    Args:
        error: Exception
        context: Context data
    """
    if not SENTRY_AVAILABLE:
        logger.error(f"Exception: {error}", exc_info=True)
        return
    
    try:
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            
            sentry_sdk.capture_exception(error)
    except Exception as e:
        logger.error(f"Failed to capture exception: {e}")


def capture_message(message: str, level: str = "info", context: Optional[Dict[str, Any]] = None):
    """
    Capture message
    
    Args:
        message: Message
        level: Level (debug, info, warning, error, fatal)
        context: Context data
    """
    if not SENTRY_AVAILABLE:
        logger.log(level.upper(), message)
        return
    
    try:
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            
            sentry_sdk.capture_message(message, level=level)
    except Exception as e:
        logger.error(f"Failed to capture message: {e}")


def set_user_context(user_id: str, email: Optional[str] = None, **kwargs):
    """
    Set user context
    
    Args:
        user_id: User ID
        email: Email
        **kwargs: Additional user data
    """
    if not SENTRY_AVAILABLE:
        return
    
    try:
        sentry_sdk.set_user({
            "id": user_id,
            "email": email,
            **kwargs
        })
    except Exception as e:
        logger.error(f"Failed to set user context: {e}")


def add_breadcrumb(message: str, category: str = "default", level: str = "info", data: Optional[Dict[str, Any]] = None):
    """
    Add breadcrumb
    
    Args:
        message: Message
        category: Category
        level: Level
        data: Additional data
    """
    if not SENTRY_AVAILABLE:
        return
    
    try:
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data
        )
    except Exception as e:
        logger.error(f"Failed to add breadcrumb: {e}")

