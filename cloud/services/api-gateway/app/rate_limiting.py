"""
Rate Limiting
محدودیت نرخ درخواست
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger
import time
from collections import defaultdict
import asyncio


@dataclass
class RateLimitRule:
    """قانون rate limiting"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst: int = 10  # تعداد درخواست‌های burst


@dataclass
class RateLimitRecord:
    """رکورد rate limiting"""
    requests: list = field(default_factory=list)
    blocked_until: Optional[datetime] = None


class RateLimiter:
    """Rate Limiter"""
    
    def __init__(self):
        """مقداردهی اولیه"""
        self.rate_limits: Dict[str, RateLimitRecord] = defaultdict(RateLimitRecord)
        self.rules: Dict[str, RateLimitRule] = {}
        self.default_rule = RateLimitRule()
        self.cleanup_interval = 3600  # 1 hour
        self._cleanup_task = None
    
    def set_rule(self, endpoint: str, rule: RateLimitRule):
        """
        تنظیم قانون برای endpoint
        
        Args:
            endpoint: مسیر endpoint
            rule: قانون rate limiting
        """
        self.rules[endpoint] = rule
        logger.info(f"Set rate limit rule for {endpoint}: {rule.requests_per_minute}/min")
    
    def get_rule(self, endpoint: str) -> RateLimitRule:
        """
        دریافت قانون برای endpoint
        
        Args:
            endpoint: مسیر endpoint
        
        Returns:
            قانون rate limiting
        """
        return self.rules.get(endpoint, self.default_rule)
    
    def get_client_identifier(self, request: Request) -> str:
        """
        شناسایی کلاینت
        
        Args:
            request: FastAPI request
        
        Returns:
            شناسه کلاینت
        """
        # استفاده از IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # یا استفاده از API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"
        
        # یا استفاده از user ID (اگر authenticated)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        return f"ip:{client_ip}"
    
    def check_rate_limit(
        self,
        client_id: str,
        endpoint: str
    ) -> Tuple[bool, Optional[Dict]]:
        """
        بررسی rate limit
        
        Args:
            client_id: شناسه کلاینت
            endpoint: مسیر endpoint
        
        Returns:
            Tuple (allowed, rate_limit_info)
        """
        key = f"{client_id}:{endpoint}"
        record = self.rate_limits[key]
        rule = self.get_rule(endpoint)
        
        now = datetime.now()
        
        # بررسی block
        if record.blocked_until and now < record.blocked_until:
            remaining_seconds = (record.blocked_until - now).total_seconds()
            return False, {
                "allowed": False,
                "retry_after": int(remaining_seconds),
                "message": "Rate limit exceeded"
            }
        
        # پاک کردن requests قدیمی
        cutoff_minute = now - timedelta(minutes=1)
        cutoff_hour = now - timedelta(hours=1)
        cutoff_day = now - timedelta(days=1)
        
        record.requests = [
            req_time for req_time in record.requests
            if req_time > cutoff_day
        ]
        
        # شمارش requests
        requests_last_minute = sum(1 for r in record.requests if r > cutoff_minute)
        requests_last_hour = sum(1 for r in record.requests if r > cutoff_hour)
        requests_last_day = len(record.requests)
        
        # بررسی limits
        if requests_last_minute >= rule.requests_per_minute:
            # Block برای 1 دقیقه
            record.blocked_until = now + timedelta(minutes=1)
            return False, {
                "allowed": False,
                "retry_after": 60,
                "message": "Rate limit exceeded: too many requests per minute"
            }
        
        if requests_last_hour >= rule.requests_per_hour:
            # Block برای 1 ساعت
            record.blocked_until = now + timedelta(hours=1)
            return False, {
                "allowed": False,
                "retry_after": 3600,
                "message": "Rate limit exceeded: too many requests per hour"
            }
        
        if requests_last_day >= rule.requests_per_day:
            # Block برای 1 روز
            record.blocked_until = now + timedelta(days=1)
            return False, {
                "allowed": False,
                "retry_after": 86400,
                "message": "Rate limit exceeded: too many requests per day"
            }
        
        # اضافه کردن request
        record.requests.append(now)
        
        # محاسبه remaining
        remaining_minute = max(0, rule.requests_per_minute - requests_last_minute - 1)
        remaining_hour = max(0, rule.requests_per_hour - requests_last_hour - 1)
        remaining_day = max(0, rule.requests_per_day - requests_last_day - 1)
        
        return True, {
            "allowed": True,
            "remaining_minute": remaining_minute,
            "remaining_hour": remaining_hour,
            "remaining_day": remaining_day,
            "reset_minute": (cutoff_minute + timedelta(minutes=1)).timestamp(),
            "reset_hour": (cutoff_hour + timedelta(hours=1)).timestamp(),
            "reset_day": (cutoff_day + timedelta(days=1)).timestamp()
        }
    
    def cleanup_old_records(self):
        """پاک کردن records قدیمی"""
        cutoff = datetime.now() - timedelta(days=1)
        
        keys_to_remove = []
        for key, record in self.rate_limits.items():
            # اگر آخرین request بیش از 1 روز پیش باشد، حذف
            if record.requests and max(record.requests) < cutoff:
                if not record.blocked_until or record.blocked_until < datetime.now():
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.rate_limits[key]
        
        if keys_to_remove:
            logger.info(f"Cleaned up {len(keys_to_remove)} old rate limit records")
    
    async def start_cleanup_task(self):
        """شروع task پاک‌سازی دوره‌ای"""
        while True:
            await asyncio.sleep(self.cleanup_interval)
            self.cleanup_old_records()


# Singleton instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """دریافت instance rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


# Middleware برای rate limiting
async def rate_limit_middleware(request: Request, call_next):
    """Middleware برای rate limiting"""
    # Skip برای health check
    if request.url.path == "/health":
        return await call_next(request)
    
    rate_limiter = get_rate_limiter()
    client_id = rate_limiter.get_client_identifier(request)
    endpoint = request.url.path
    
    allowed, info = rate_limiter.check_rate_limit(client_id, endpoint)
    
    if not allowed:
        # اضافه کردن headers
        response = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": info.get("message"),
                "retry_after": info.get("retry_after")
            }
        )
        response.headers["Retry-After"] = str(info.get("retry_after", 60))
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.get_rule(endpoint).requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = "0"
        return response
    
    # ادامه request
    response = await call_next(request)
    
    # اضافه کردن rate limit headers
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.get_rule(endpoint).requests_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(info.get("remaining_minute", 0))
    response.headers["X-RateLimit-Reset"] = str(int(info.get("reset_minute", 0)))
    
    return response

