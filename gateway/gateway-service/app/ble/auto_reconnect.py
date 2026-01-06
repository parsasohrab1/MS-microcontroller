"""
Auto-Reconnection Mechanism for BLE
مکانیزم اتصال مجدد خودکار برای BLE
"""

import asyncio
from typing import Optional, Callable, Dict
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger

from bleak import BleakClient
from bleak.backends.device import BLEDevice


class ReconnectStrategy(Enum):
    """استراتژی اتصال مجدد"""
    IMMEDIATE = "immediate"  # فوری
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # تاخیر تصاعدی
    FIXED_INTERVAL = "fixed_interval"  # تاخیر ثابت
    CUSTOM = "custom"  # سفارشی


class AutoReconnectManager:
    """مدیریت اتصال مجدد خودکار"""
    
    def __init__(
        self,
        max_reconnect_attempts: int = 10,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        strategy: ReconnectStrategy = ReconnectStrategy.EXPONENTIAL_BACKOFF,
        custom_delays: Optional[list[float]] = None
    ):
        """
        مقداردهی اولیه
        
        Args:
            max_reconnect_attempts: حداکثر تلاش برای اتصال مجدد
            initial_delay: تاخیر اولیه (ثانیه)
            max_delay: حداکثر تاخیر (ثانیه)
            strategy: استراتژی اتصال مجدد
            custom_delays: لیست تاخیرهای سفارشی
        """
        self.max_reconnect_attempts = max_reconnect_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.custom_delays = custom_delays or []
        
        self._reconnect_tasks: Dict[str, asyncio.Task] = {}
        self._reconnect_callbacks: Dict[str, Callable] = {}
        self._reconnect_counts: Dict[str, int] = {}
    
    def register_device(
        self,
        device_address: str,
        reconnect_callback: Callable[[str], asyncio.Coroutine],
        auto_start: bool = True
    ):
        """
        ثبت دستگاه برای auto-reconnect
        
        Args:
            device_address: آدرس دستگاه
            reconnect_callback: تابع callback برای اتصال مجدد
            auto_start: شروع خودکار
        """
        self._reconnect_callbacks[device_address] = reconnect_callback
        self._reconnect_counts[device_address] = 0
        
        if auto_start:
            self.start_reconnect(device_address)
    
    def start_reconnect(self, device_address: str):
        """شروع اتصال مجدد برای دستگاه"""
        if device_address in self._reconnect_tasks:
            # قبلاً در حال اتصال مجدد است
            return
        
        async def reconnect_loop():
            """حلقه اتصال مجدد"""
            attempt = 0
            
            while attempt < self.max_reconnect_attempts:
                try:
                    # محاسبه تاخیر
                    delay = self._calculate_delay(attempt)
                    
                    if delay > 0:
                        logger.info(
                            f"Reconnecting to {device_address} "
                            f"in {delay:.1f}s (attempt {attempt + 1}/{self.max_reconnect_attempts})"
                        )
                        await asyncio.sleep(delay)
                    
                    # تلاش برای اتصال مجدد
                    callback = self._reconnect_callbacks.get(device_address)
                    if callback:
                        success = await callback(device_address)
                        
                        if success:
                            logger.info(f"Successfully reconnected to {device_address}")
                            self._reconnect_counts[device_address] = attempt + 1
                            self.stop_reconnect(device_address)
                            return
                    
                    attempt += 1
                    
                except asyncio.CancelledError:
                    logger.info(f"Reconnect cancelled for {device_address}")
                    return
                except Exception as e:
                    logger.error(f"Error in reconnect loop for {device_address}: {e}")
                    attempt += 1
            
            # تمام تلاش‌ها ناموفق
            logger.error(
                f"Failed to reconnect to {device_address} "
                f"after {self.max_reconnect_attempts} attempts"
            )
            self.stop_reconnect(device_address)
        
        self._reconnect_tasks[device_address] = asyncio.create_task(reconnect_loop())
    
    def stop_reconnect(self, device_address: str):
        """توقف اتصال مجدد"""
        if device_address in self._reconnect_tasks:
            task = self._reconnect_tasks[device_address]
            task.cancel()
            del self._reconnect_tasks[device_address]
    
    def _calculate_delay(self, attempt: int) -> float:
        """محاسبه تاخیر بر اساس استراتژی"""
        if self.strategy == ReconnectStrategy.IMMEDIATE:
            return 0.0
        
        elif self.strategy == ReconnectStrategy.EXPONENTIAL_BACKOFF:
            delay = self.initial_delay * (2 ** attempt)
            return min(delay, self.max_delay)
        
        elif self.strategy == ReconnectStrategy.FIXED_INTERVAL:
            return self.initial_delay
        
        elif self.strategy == ReconnectStrategy.CUSTOM:
            if attempt < len(self.custom_delays):
                return self.custom_delays[attempt]
            return self.max_delay
        
        return self.initial_delay
    
    def get_reconnect_count(self, device_address: str) -> int:
        """دریافت تعداد تلاش‌های اتصال مجدد"""
        return self._reconnect_counts.get(device_address, 0)
    
    def is_reconnecting(self, device_address: str) -> bool:
        """بررسی اینکه آیا در حال اتصال مجدد است"""
        return device_address in self._reconnect_tasks


# Singleton instance
_reconnect_manager: Optional[AutoReconnectManager] = None


def get_reconnect_manager() -> AutoReconnectManager:
    """دریافت instance Reconnect Manager"""
    global _reconnect_manager
    if _reconnect_manager is None:
        _reconnect_manager = AutoReconnectManager()
    return _reconnect_manager

