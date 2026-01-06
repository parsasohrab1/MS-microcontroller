"""
BLE Connection Pool
مدیریت pool اتصالات BLE برای بهبود کارایی
"""

import asyncio
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
from loguru import logger

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice


class ConnectionState(Enum):
    """وضعیت اتصال"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    ERROR = "error"


@dataclass
class ConnectionInfo:
    """اطلاعات اتصال"""
    device_address: str
    device_name: Optional[str] = None
    client: Optional[BleakClient] = None
    state: ConnectionState = ConnectionState.DISCONNECTED
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    connection_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class BLEConnectionPool:
    """Connection Pool برای مدیریت اتصالات BLE"""
    
    def __init__(
        self,
        max_connections: int = 10,
        connection_timeout: float = 10.0,
        idle_timeout: float = 300.0,  # 5 minutes
        max_retries: int = 3,
        retry_delay: float = 2.0
    ):
        """
        مقداردهی اولیه Connection Pool
        
        Args:
            max_connections: حداکثر تعداد اتصالات همزمان
            connection_timeout: زمان انتظار برای اتصال (ثانیه)
            idle_timeout: زمان idle قبل از بستن اتصال (ثانیه)
            max_retries: حداکثر تلاش برای اتصال
            retry_delay: تاخیر بین تلاش‌ها (ثانیه)
        """
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.idle_timeout = idle_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self._connections: Dict[str, ConnectionInfo] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # شروع task پاکسازی
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """شروع task پاکسازی اتصالات idle"""
        async def cleanup_idle_connections():
            while True:
                try:
                    await asyncio.sleep(60)  # بررسی هر 60 ثانیه
                    await self._cleanup_idle_connections()
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_idle_connections())
    
    async def _cleanup_idle_connections(self):
        """پاکسازی اتصالات idle"""
        async with self._lock:
            now = datetime.now()
            to_remove = []
            
            for address, conn_info in self._connections.items():
                if conn_info.state == ConnectionState.CONNECTED:
                    idle_time = (now - conn_info.last_used).total_seconds()
                    if idle_time > self.idle_timeout:
                        logger.info(f"Closing idle connection: {address}")
                        to_remove.append(address)
            
            for address in to_remove:
                await self._close_connection(address)
    
    async def get_connection(
        self,
        device_address: str,
        device_name: Optional[str] = None
    ) -> Optional[BleakClient]:
        """
        دریافت اتصال از pool (یا ایجاد جدید)
        
        Args:
            device_address: آدرس دستگاه BLE
            device_name: نام دستگاه (اختیاری)
        
        Returns:
            BleakClient یا None در صورت خطا
        """
        async with self._lock:
            # بررسی وجود اتصال
            if device_address in self._connections:
                conn_info = self._connections[device_address]
                
                # اگر اتصال فعال است
                if conn_info.state == ConnectionState.CONNECTED:
                    if conn_info.client and conn_info.client.is_connected:
                        conn_info.last_used = datetime.now()
                        return conn_info.client
                    else:
                        # اتصال قطع شده
                        conn_info.state = ConnectionState.DISCONNECTED
            
            # بررسی تعداد اتصالات
            active_connections = sum(
                1 for c in self._connections.values()
                if c.state == ConnectionState.CONNECTED
            )
            
            if active_connections >= self.max_connections:
                logger.warning(f"Max connections reached ({self.max_connections})")
                return None
            
            # ایجاد اتصال جدید
            return await self._create_connection(device_address, device_name)
    
    async def _create_connection(
        self,
        device_address: str,
        device_name: Optional[str] = None
    ) -> Optional[BleakClient]:
        """ایجاد اتصال جدید"""
        conn_info = ConnectionInfo(
            device_address=device_address,
            device_name=device_name,
            state=ConnectionState.CONNECTING
        )
        
        self._connections[device_address] = conn_info
        
        # تلاش برای اتصال
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Connecting to {device_address} (attempt {attempt + 1}/{self.max_retries})")
                
                # جستجوی دستگاه
                device = await BleakScanner.find_device_by_address(
                    device_address,
                    timeout=self.connection_timeout
                )
                
                if not device:
                    raise Exception(f"Device {device_address} not found")
                
                # ایجاد client
                client = BleakClient(device)
                
                # اتصال
                await asyncio.wait_for(
                    client.connect(),
                    timeout=self.connection_timeout
                )
                
                if client.is_connected:
                    conn_info.client = client
                    conn_info.state = ConnectionState.CONNECTED
                    conn_info.connection_count += 1
                    conn_info.last_used = datetime.now()
                    logger.info(f"Connected to {device_address}")
                    return client
                
            except asyncio.TimeoutError:
                conn_info.error_count += 1
                conn_info.last_error = "Connection timeout"
                logger.warning(f"Connection timeout for {device_address}")
            except Exception as e:
                conn_info.error_count += 1
                conn_info.last_error = str(e)
                logger.error(f"Connection error for {device_address}: {e}")
            
            # تاخیر قبل از تلاش بعدی
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        # تمام تلاش‌ها ناموفق
        conn_info.state = ConnectionState.ERROR
        logger.error(f"Failed to connect to {device_address} after {self.max_retries} attempts")
        return None
    
    async def release_connection(self, device_address: str):
        """
        آزاد کردن اتصال (بازگشت به pool)
        
        Args:
            device_address: آدرس دستگاه
        """
        async with self._lock:
            if device_address in self._connections:
                conn_info = self._connections[device_address]
                conn_info.last_used = datetime.now()
                # اتصال در pool باقی می‌ماند برای استفاده بعدی
    
    async def close_connection(self, device_address: str):
        """
        بستن اتصال
        
        Args:
            device_address: آدرس دستگاه
        """
        async with self._lock:
            await self._close_connection(device_address)
    
    async def _close_connection(self, device_address: str):
        """بستن اتصال (internal)"""
        if device_address in self._connections:
            conn_info = self._connections[device_address]
            
            if conn_info.client and conn_info.client.is_connected:
                try:
                    conn_info.state = ConnectionState.DISCONNECTING
                    await conn_info.client.disconnect()
                    logger.info(f"Disconnected from {device_address}")
                except Exception as e:
                    logger.error(f"Error disconnecting from {device_address}: {e}")
            
            conn_info.state = ConnectionState.DISCONNECTED
            conn_info.client = None
    
    async def close_all(self):
        """بستن تمام اتصالات"""
        async with self._lock:
            addresses = list(self._connections.keys())
            for address in addresses:
                await self._close_connection(address)
            self._connections.clear()
        
        # توقف task پاکسازی
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    def get_connection_info(self, device_address: str) -> Optional[ConnectionInfo]:
        """دریافت اطلاعات اتصال"""
        return self._connections.get(device_address)
    
    def get_pool_stats(self) -> Dict[str, any]:
        """دریافت آمار pool"""
        total = len(self._connections)
        connected = sum(
            1 for c in self._connections.values()
            if c.state == ConnectionState.CONNECTED
        )
        connecting = sum(
            1 for c in self._connections.values()
            if c.state == ConnectionState.CONNECTING
        )
        errors = sum(c.error_count for c in self._connections.values())
        
        return {
            "total_connections": total,
            "connected": connected,
            "connecting": connecting,
            "total_errors": errors,
            "max_connections": self.max_connections
        }


# Singleton instance
_connection_pool: Optional[BLEConnectionPool] = None


def get_connection_pool() -> BLEConnectionPool:
    """دریافت instance Connection Pool"""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = BLEConnectionPool()
    return _connection_pool

