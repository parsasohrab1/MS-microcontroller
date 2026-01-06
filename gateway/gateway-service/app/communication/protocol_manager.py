"""
Protocol Manager
مدیریت پروتکل‌های ارتباطی مختلف (BLE, Wi-Fi, Cellular, NFC)
"""

from typing import Optional, Dict, List, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import asyncio
from loguru import logger

from ..ble.connection_pool import get_connection_pool
from .wifi_manager import WiFiManager
from .cellular_manager import CellularManager
from .nfc_manager import NFCManager


class ProtocolType(str, Enum):
    """نوع پروتکل"""
    BLE = "ble"
    WIFI = "wifi"
    CELLULAR = "cellular"
    NFC = "nfc"


@dataclass
class ConnectionInfo:
    """اطلاعات اتصال"""
    protocol: ProtocolType
    device_id: str
    connected: bool
    signal_strength: Optional[float] = None  # برای Wi-Fi/Cellular
    bandwidth: Optional[float] = None  # Mbps
    latency: Optional[float] = None  # ms
    last_connected: Optional[datetime] = None


class ProtocolManager:
    """مدیریت پروتکل‌های ارتباطی"""
    
    def __init__(self):
        """مقداردهی اولیه"""
        self.active_connections: Dict[str, ConnectionInfo] = {}
        self.protocol_handlers = {
            ProtocolType.BLE: self._handle_ble,
            ProtocolType.WIFI: self._handle_wifi,
            ProtocolType.CELLULAR: self._handle_cellular,
            ProtocolType.NFC: self._handle_nfc,
        }
        
        # Managers
        self.wifi_manager = WiFiManager()
        self.cellular_manager = CellularManager()
        self.nfc_manager = NFCManager()
        self.ble_pool = get_connection_pool()
    
    async def connect(
        self,
        protocol: ProtocolType,
        device_id: str,
        config: Optional[Dict] = None
    ) -> bool:
        """
        اتصال با استفاده از پروتکل مشخص
        
        Args:
            protocol: نوع پروتکل
            device_id: شناسه دستگاه
            config: تنظیمات اتصال
        
        Returns:
            True در صورت موفقیت
        """
        try:
            handler = self.protocol_handlers.get(protocol)
            if not handler:
                logger.error(f"Unsupported protocol: {protocol}")
                return False
            
            success = await handler(device_id, config or {})
            
            if success:
                self.active_connections[device_id] = ConnectionInfo(
                    protocol=protocol,
                    device_id=device_id,
                    connected=True,
                    last_connected=datetime.now()
                )
                logger.info(f"Connected via {protocol.value} to {device_id}")
            
            return success
        
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    async def disconnect(self, device_id: str) -> bool:
        """قطع اتصال"""
        if device_id not in self.active_connections:
            return False
        
        conn_info = self.active_connections[device_id]
        
        try:
            if conn_info.protocol == ProtocolType.BLE:
                await self.ble_pool.close_connection(device_id)
            elif conn_info.protocol == ProtocolType.WIFI:
                await self.wifi_manager.disconnect(device_id)
            elif conn_info.protocol == ProtocolType.CELLULAR:
                await self.cellular_manager.disconnect(device_id)
            elif conn_info.protocol == ProtocolType.NFC:
                await self.nfc_manager.disconnect(device_id)
            
            conn_info.connected = False
            logger.info(f"Disconnected from {device_id}")
            return True
        
        except Exception as e:
            logger.error(f"Disconnection error: {e}")
            return False
    
    async def send_data(
        self,
        device_id: str,
        data: bytes,
        priority: int = 0
    ) -> bool:
        """
        ارسال داده
        
        Args:
            device_id: شناسه دستگاه
            data: داده برای ارسال
            priority: اولویت (0=normal, 1=high, 2=critical)
        
        Returns:
            True در صورت موفقیت
        """
        if device_id not in self.active_connections:
            logger.error(f"Device {device_id} not connected")
            return False
        
        conn_info = self.active_connections[device_id]
        
        try:
            if conn_info.protocol == ProtocolType.BLE:
                return await self._send_via_ble(device_id, data, priority)
            elif conn_info.protocol == ProtocolType.WIFI:
                return await self._send_via_wifi(device_id, data, priority)
            elif conn_info.protocol == ProtocolType.CELLULAR:
                return await self._send_via_cellular(device_id, data, priority)
            elif conn_info.protocol == ProtocolType.NFC:
                return await self._send_via_nfc(device_id, data, priority)
            
            return False
        
        except Exception as e:
            logger.error(f"Send data error: {e}")
            return False
    
    async def receive_data(self, device_id: str, timeout: float = 5.0) -> Optional[bytes]:
        """دریافت داده"""
        if device_id not in self.active_connections:
            return None
        
        conn_info = self.active_connections[device_id]
        
        try:
            if conn_info.protocol == ProtocolType.BLE:
                return await self._receive_via_ble(device_id, timeout)
            elif conn_info.protocol == ProtocolType.WIFI:
                return await self._receive_via_wifi(device_id, timeout)
            elif conn_info.protocol == ProtocolType.CELLULAR:
                return await self._receive_via_cellular(device_id, timeout)
            
            return None
        
        except Exception as e:
            logger.error(f"Receive data error: {e}")
            return None
    
    def select_best_protocol(self, device_id: str) -> ProtocolType:
        """
        انتخاب بهترین پروتکل بر اساس شرایط
        
        Args:
            device_id: شناسه دستگاه
        
        Returns:
            بهترین پروتکل
        """
        # بررسی دسترسی‌پذیری پروتکل‌ها
        available_protocols = []
        
        # BLE همیشه در دسترس است (برای pairing اولیه)
        available_protocols.append((ProtocolType.BLE, 1.0))
        
        # Wi-Fi
        if self.wifi_manager.is_available():
            signal_strength = self.wifi_manager.get_signal_strength()
            available_protocols.append((ProtocolType.WIFI, signal_strength))
        
        # Cellular
        if self.cellular_manager.is_available():
            signal_strength = self.cellular_manager.get_signal_strength()
            available_protocols.append((ProtocolType.CELLULAR, signal_strength))
        
        # انتخاب بهترین (بالاترین signal strength)
        if available_protocols:
            best = max(available_protocols, key=lambda x: x[1])
            return best[0]
        
        return ProtocolType.BLE  # Fallback به BLE
    
    async def auto_switch_protocol(self, device_id: str) -> bool:
        """
        تغییر خودکار پروتکل در صورت نیاز
        
        Args:
            device_id: شناسه دستگاه
        
        Returns:
            True اگر تغییر انجام شد
        """
        if device_id not in self.active_connections:
            return False
        
        current_conn = self.active_connections[device_id]
        
        # بررسی کیفیت اتصال فعلی
        if current_conn.protocol == ProtocolType.BLE:
            # اگر داده حجیم است، به Wi-Fi تغییر می‌دهیم
            if current_conn.bandwidth and current_conn.bandwidth < 1.0:  # کمتر از 1 Mbps
                if self.wifi_manager.is_available():
                    await self.disconnect(device_id)
                    return await self.connect(ProtocolType.WIFI, device_id)
        
        return False
    
    # Protocol handlers
    async def _handle_ble(self, device_id: str, config: Dict) -> bool:
        """Handler برای BLE"""
        client = await self.ble_pool.get_connection(device_id)
        return client is not None
    
    async def _handle_wifi(self, device_id: str, config: Dict) -> bool:
        """Handler برای Wi-Fi"""
        ssid = config.get('ssid')
        password = config.get('password')
        return await self.wifi_manager.connect(device_id, ssid, password)
    
    async def _handle_cellular(self, device_id: str, config: Dict) -> bool:
        """Handler برای Cellular"""
        apn = config.get('apn', 'internet')
        return await self.cellular_manager.connect(device_id, apn)
    
    async def _handle_nfc(self, device_id: str, config: Dict) -> bool:
        """Handler برای NFC"""
        return await self.nfc_manager.pair(device_id)
    
    # Send/Receive methods
    async def _send_via_ble(self, device_id: str, data: bytes, priority: int) -> bool:
        """ارسال از طریق BLE"""
        client = await self.ble_pool.get_connection(device_id)
        if not client:
            return False
        
        # TODO: پیاده‌سازی ارسال واقعی
        return True
    
    async def _send_via_wifi(self, device_id: str, data: bytes, priority: int) -> bool:
        """ارسال از طریق Wi-Fi"""
        return await self.wifi_manager.send_data(device_id, data, priority)
    
    async def _send_via_cellular(self, device_id: str, data: bytes, priority: int) -> bool:
        """ارسال از طریق Cellular"""
        return await self.cellular_manager.send_data(device_id, data, priority)
    
    async def _send_via_nfc(self, device_id: str, data: bytes, priority: int) -> bool:
        """ارسال از طریق NFC (برای داده‌های کوچک)"""
        return await self.nfc_manager.send_data(device_id, data)
    
    async def _receive_via_ble(self, device_id: str, timeout: float) -> Optional[bytes]:
        """دریافت از طریق BLE"""
        # TODO: پیاده‌سازی
        return None
    
    async def _receive_via_wifi(self, device_id: str, timeout: float) -> Optional[bytes]:
        """دریافت از طریق Wi-Fi"""
        return await self.wifi_manager.receive_data(device_id, timeout)
    
    async def _receive_via_cellular(self, device_id: str, timeout: float) -> Optional[bytes]:
        """دریافت از طریق Cellular"""
        return await self.cellular_manager.receive_data(device_id, timeout)
    
    def get_connection_info(self, device_id: str) -> Optional[ConnectionInfo]:
        """دریافت اطلاعات اتصال"""
        return self.active_connections.get(device_id)
    
    def get_all_connections(self) -> List[ConnectionInfo]:
        """دریافت تمام اتصالات"""
        return list(self.active_connections.values())


# Singleton instance
_protocol_manager: Optional[ProtocolManager] = None


def get_protocol_manager() -> ProtocolManager:
    """دریافت instance Protocol Manager"""
    global _protocol_manager
    if _protocol_manager is None:
        _protocol_manager = ProtocolManager()
    return _protocol_manager

