"""
Redis Client - Caching, Session Management, Rate Limiting
کلاینت Redis برای کش، مدیریت session و rate limiting
"""

import redis
import json
from typing import Optional, Any, Dict, List
from datetime import timedelta
from loguru import logger
import os
import hashlib
import time


class RedisClient:
    """کلاینت Redis برای کش و سایر عملیات"""
    
    def __init__(self, connection_url: Optional[str] = None):
        """
        مقداردهی اولیه کلاینت
        
        Args:
            connection_url: URL اتصال Redis
                مثال: redis://localhost:6379/0
        """
        self.connection_url = connection_url or os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0"
        )
        self.client: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self):
        """اتصال به Redis"""
        try:
            self.client = redis.from_url(
                self.connection_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # تست اتصال
            self.client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _ensure_connection(self):
        """اطمینان از اتصال"""
        try:
            self.client.ping()
        except:
            self._connect()
    
    # ========================================================================
    # Cache Operations
    # ========================================================================
    
    def set_cache(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """
        ذخیره در cache
        
        Args:
            key: کلید
            value: مقدار
            ttl: زمان انقضا (ثانیه)
            serialize: آیا باید JSON serialize شود
        
        Returns:
            True در صورت موفقیت
        """
        self._ensure_connection()
        
        try:
            if serialize:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                else:
                    value = str(value)
            
            if ttl:
                return self.client.setex(key, ttl, value)
            else:
                return self.client.set(key, value)
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False
    
    def get_cache(
        self,
        key: str,
        deserialize: bool = True,
        default: Any = None
    ) -> Any:
        """
        دریافت از cache
        
        Args:
            key: کلید
            deserialize: آیا باید JSON deserialize شود
            default: مقدار پیش‌فرض در صورت عدم وجود
        
        Returns:
            مقدار یا default
        """
        self._ensure_connection()
        
        try:
            value = self.client.get(key)
            if value is None:
                return default
            
            if deserialize:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            
            return value
        except Exception as e:
            logger.error(f"Failed to get cache: {e}")
            return default
    
    def delete_cache(self, *keys: str) -> int:
        """
        حذف از cache
        
        Args:
            *keys: کلیدها
        
        Returns:
            تعداد کلیدهای حذف شده
        """
        self._ensure_connection()
        
        try:
            return self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")
            return 0
    
    def exists_cache(self, key: str) -> bool:
        """بررسی وجود کلید"""
        self._ensure_connection()
        return bool(self.client.exists(key))
    
    def clear_cache_pattern(self, pattern: str) -> int:
        """
        حذف کلیدها بر اساس pattern
        
        Args:
            pattern: الگو (مثلاً "user:*")
        
        Returns:
            تعداد کلیدهای حذف شده
        """
        self._ensure_connection()
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to clear cache pattern: {e}")
            return 0
    
    # ========================================================================
    # Session Management
    # ========================================================================
    
    def set_session(
        self,
        session_id: str,
        user_id: int,
        data: Optional[Dict[str, Any]] = None,
        ttl: int = 3600  # 1 hour default
    ) -> bool:
        """
        ذخیره session
        
        Args:
            session_id: شناسه session
            user_id: شناسه کاربر
            data: داده‌های اضافی
            ttl: زمان انقضا (ثانیه)
        """
        session_key = f"session:{session_id}"
        session_data = {
            "user_id": user_id,
            "created_at": time.time(),
            "data": data or {}
        }
        return self.set_cache(session_key, session_data, ttl=ttl)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """دریافت session"""
        session_key = f"session:{session_id}"
        return self.get_cache(session_key)
    
    def delete_session(self, session_id: str) -> bool:
        """حذف session"""
        session_key = f"session:{session_id}"
        return bool(self.delete_cache(session_key))
    
    def extend_session(self, session_id: str, ttl: int = 3600) -> bool:
        """تمدید session"""
        session_key = f"session:{session_id}"
        self._ensure_connection()
        return bool(self.client.expire(session_key, ttl))
    
    # ========================================================================
    # Rate Limiting
    # ========================================================================
    
    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
        action: str = "request"
    ) -> tuple[bool, int, int]:
        """
        بررسی rate limit
        
        Args:
            identifier: شناسه (IP, user_id, etc.)
            max_requests: حداکثر درخواست‌ها
            window_seconds: پنجره زمانی (ثانیه)
            action: نوع action (برای namespace)
        
        Returns:
            (allowed, remaining, reset_time)
        """
        self._ensure_connection()
        
        key = f"ratelimit:{action}:{identifier}"
        current_time = int(time.time())
        window_start = current_time - (current_time % window_seconds)
        window_key = f"{key}:{window_start}"
        
        try:
            # افزایش counter
            count = self.client.incr(window_key)
            
            # تنظیم TTL برای اولین بار
            if count == 1:
                self.client.expire(window_key, window_seconds)
            
            # بررسی limit
            allowed = count <= max_requests
            remaining = max(0, max_requests - count)
            reset_time = window_start + window_seconds
            
            return allowed, remaining, reset_time
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # در صورت خطا، اجازه می‌دهیم
            return True, max_requests, current_time + window_seconds
    
    def get_rate_limit_info(
        self,
        identifier: str,
        window_seconds: int,
        action: str = "request"
    ) -> Dict[str, Any]:
        """دریافت اطلاعات rate limit"""
        self._ensure_connection()
        
        key = f"ratelimit:{action}:{identifier}"
        current_time = int(time.time())
        window_start = current_time - (current_time % window_seconds)
        window_key = f"{key}:{window_start}"
        
        try:
            count = self.client.get(window_key)
            count = int(count) if count else 0
            reset_time = window_start + window_seconds
            
            return {
                "count": count,
                "reset_time": reset_time,
                "remaining_seconds": reset_time - current_time
            }
        except Exception as e:
            logger.error(f"Failed to get rate limit info: {e}")
            return {"count": 0, "reset_time": 0, "remaining_seconds": 0}
    
    # ========================================================================
    # Real-time Analytics
    # ========================================================================
    
    def increment_counter(
        self,
        key: str,
        amount: int = 1,
        ttl: Optional[int] = None
    ) -> int:
        """
        افزایش counter
        
        Args:
            key: کلید counter
            amount: مقدار افزایش
            ttl: زمان انقضا (اختیاری)
        
        Returns:
            مقدار جدید counter
        """
        self._ensure_connection()
        
        try:
            value = self.client.incrby(key, amount)
            if ttl and value == amount:  # فقط برای اولین بار
                self.client.expire(key, ttl)
            return value
        except Exception as e:
            logger.error(f"Failed to increment counter: {e}")
            return 0
    
    def get_counter(self, key: str) -> int:
        """دریافت مقدار counter"""
        self._ensure_connection()
        try:
            value = self.client.get(key)
            return int(value) if value else 0
        except:
            return 0
    
    def add_to_set(self, key: str, *values: str, ttl: Optional[int] = None) -> int:
        """اضافه کردن به set"""
        self._ensure_connection()
        try:
            count = self.client.sadd(key, *values)
            if ttl:
                self.client.expire(key, ttl)
            return count
        except Exception as e:
            logger.error(f"Failed to add to set: {e}")
            return 0
    
    def get_set_members(self, key: str) -> List[str]:
        """دریافت اعضای set"""
        self._ensure_connection()
        try:
            return list(self.client.smembers(key))
        except:
            return []
    
    def add_to_sorted_set(
        self,
        key: str,
        score: float,
        value: str,
        ttl: Optional[int] = None
    ) -> bool:
        """اضافه کردن به sorted set"""
        self._ensure_connection()
        try:
            result = self.client.zadd(key, {value: score})
            if ttl:
                self.client.expire(key, ttl)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to add to sorted set: {e}")
            return False
    
    def get_sorted_set_range(
        self,
        key: str,
        start: int = 0,
        end: int = -1,
        reverse: bool = False
    ) -> List[str]:
        """دریافت range از sorted set"""
        self._ensure_connection()
        try:
            if reverse:
                return list(self.client.zrevrange(key, start, end))
            else:
                return list(self.client.zrange(key, start, end))
        except:
            return []
    
    def close(self):
        """بستن اتصال"""
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")


# Singleton instance
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """دریافت instance کلاینت Redis"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client

