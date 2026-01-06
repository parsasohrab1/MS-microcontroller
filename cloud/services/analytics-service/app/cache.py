"""
Cache Integration
"""

from typing import Optional, Dict, Any
import json
from loguru import logger
import sys
import os

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

try:
    from redis_client import RedisClient
    
    # Initialize client
    redis_client = RedisClient()
except ImportError:
    logger.warning("Redis client not available")
    redis_client = None


async def get_from_cache(key: str) -> Optional[Dict]:
    """
    دریافت از cache
    
    Args:
        key: کلید
    
    Returns:
        داده یا None
    """
    if not redis_client:
        return None
    
    try:
        value = await redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error(f"Error getting from cache: {e}")
        return None


async def set_to_cache(key: str, value: Dict, ttl: int = 3600):
    """
    ذخیره در cache
    
    Args:
        key: کلید
        value: مقدار
        ttl: زمان انقضا (ثانیه)
    """
    if not redis_client:
        return
    
    try:
        await redis_client.set(key, json.dumps(value), ttl=ttl)
    except Exception as e:
        logger.error(f"Error setting cache: {e}")

