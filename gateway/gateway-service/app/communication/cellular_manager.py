"""
Cellular Manager
مدیریت اتصالات Cellular (4G/5G) برای مناطق دور
"""

import asyncio
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
import serial
import serial.tools.list_ports


@dataclass
class CellularInfo:
    """اطلاعات Cellular"""
    operator: str
    signal_strength: int  # dBm
    network_type: str  # 4G, 5G, LTE, etc.
    connected: bool = False
    ip_address: Optional[str] = None


class CellularManager:
    """مدیریت Cellular"""
    
    def __init__(self, modem_port: Optional[str] = None):
        """
        مقداردهی اولیه
        
        Args:
            modem_port: پورت سریال مودم (اختیاری - auto-detect)
        """
        self.modem_port = modem_port or self._detect_modem()
        self.serial_connection: Optional[serial.Serial] = None
        self.cellular_info: Optional[CellularInfo] = None
        self.connected_devices: Dict[str, any] = {}
    
    def _detect_modem(self) -> Optional[str]:
        """تشخیص خودکار پورت مودم"""
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            # جستجوی مودم‌های شناخته شده
            if any(keyword in port.description.lower() for keyword in ['modem', 'cellular', 'lte', '4g', '5g']):
                logger.info(f"Detected modem on {port.device}")
                return port.device
        
        return None
    
    def is_available(self) -> bool:
        """بررسی دسترسی‌پذیری Cellular"""
        if not self.modem_port:
            return False
        
        try:
            # تست اتصال سریال
            test_serial = serial.Serial(self.modem_port, 115200, timeout=1)
            test_serial.close()
            return True
        except:
            return False
    
    def get_signal_strength(self) -> float:
        """دریافت قدرت سیگنال (0-1)"""
        if not self.cellular_info:
            return 0.0
        
        # تبدیل dBm به 0-1 scale
        # -50 dBm = 1.0, -120 dBm = 0.0
        dbm = self.cellular_info.signal_strength
        normalized = (dbm + 120) / 70  # -50 to -120 range
        return max(0.0, min(1.0, normalized))
    
    async def connect(self, device_id: str, apn: str = "internet") -> bool:
        """
        اتصال به شبکه Cellular
        
        Args:
            device_id: شناسه دستگاه
            apn: Access Point Name
        
        Returns:
            True در صورت موفقیت
        """
        if not self.modem_port:
            logger.error("No modem port available")
            return False
        
        try:
            # باز کردن اتصال سریال
            self.serial_connection = serial.Serial(
                self.modem_port,
                115200,
                timeout=5
            )
            
            # دستورات AT برای اتصال
            await self._send_at_command("AT")
            await asyncio.sleep(0.1)
            
            # تنظیم APN
            await self._send_at_command(f'AT+CGDCONT=1,"IP","{apn}"')
            await asyncio.sleep(0.1)
            
            # فعال‌سازی PDP context
            await self._send_at_command("AT+CGACT=1,1")
            await asyncio.sleep(2)
            
            # دریافت IP
            response = await self._send_at_command("AT+CGPADDR=1")
            ip_address = self._parse_ip_address(response)
            
            if ip_address:
                self.cellular_info = CellularInfo(
                    operator="",  # TODO: دریافت از AT+COPS?
                    signal_strength=await self._get_signal_strength(),
                    network_type=await self._get_network_type(),
                    connected=True,
                    ip_address=ip_address
                )
                
                self.connected_devices[device_id] = {
                    "ip": ip_address,
                    "connected_at": datetime.now()
                }
                
                logger.info(f"Connected to cellular network, IP: {ip_address}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Cellular connection error: {e}")
            return False
    
    async def disconnect(self, device_id: str) -> bool:
        """قطع اتصال"""
        try:
            if self.serial_connection:
                # غیرفعال کردن PDP context
                await self._send_at_command("AT+CGACT=0,1")
                self.serial_connection.close()
                self.serial_connection = None
            
            if device_id in self.connected_devices:
                del self.connected_devices[device_id]
            
            if self.cellular_info:
                self.cellular_info.connected = False
            
            return True
        
        except Exception as e:
            logger.error(f"Disconnection error: {e}")
            return False
    
    async def send_data(self, device_id: str, data: bytes, priority: int = 0) -> bool:
        """ارسال داده از طریق Cellular"""
        if device_id not in self.connected_devices:
            return False
        
        try:
            # استفاده از HTTP POST یا TCP socket
            # برای سادگی، از HTTP استفاده می‌کنیم
            import aiohttp
            
            device_info = self.connected_devices[device_id]
            server_url = f"https://api.example.com/data"  # TODO: از config
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    server_url,
                    json={
                        "device_id": device_id,
                        "data": data.hex(),  # تبدیل به hex string
                        "priority": priority
                    },
                    headers={"Authorization": f"Bearer {device_info.get('token', '')}"}
                ) as response:
                    return response.status == 200
        
        except Exception as e:
            logger.error(f"Error sending data via cellular: {e}")
            return False
    
    async def receive_data(self, device_id: str, timeout: float = 5.0) -> Optional[bytes]:
        """دریافت داده از طریق Cellular"""
        # معمولاً از طریق polling از سرور
        # یا WebSocket
        # TODO: پیاده‌سازی
        return None
    
    async def _send_at_command(self, command: str) -> str:
        """ارسال دستور AT"""
        if not self.serial_connection:
            return ""
        
        try:
            self.serial_connection.write(f"{command}\r\n".encode())
            await asyncio.sleep(0.1)
            
            response = b""
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < 2.0:
                if self.serial_connection.in_waiting:
                    chunk = self.serial_connection.read(self.serial_connection.in_waiting)
                    response += chunk
                    if b"OK" in response or b"ERROR" in response:
                        break
                await asyncio.sleep(0.1)
            
            return response.decode('utf-8', errors='ignore')
        
        except Exception as e:
            logger.error(f"AT command error: {e}")
            return ""
    
    def _parse_ip_address(self, response: str) -> Optional[str]:
        """استخراج IP از پاسخ AT"""
        # فرمت: +CGPADDR: 1,"192.168.1.1"
        import re
        match = re.search(r'"([\d.]+)"', response)
        if match:
            return match.group(1)
        return None
    
    async def _get_signal_strength(self) -> int:
        """دریافت قدرت سیگنال"""
        response = await self._send_at_command("AT+CSQ")
        # فرمت: +CSQ: 20,0
        import re
        match = re.search(r'\+CSQ:\s*(\d+)', response)
        if match:
            rssi = int(match.group(1))
            # تبدیل به dBm: -113 + (rssi * 2)
            return -113 + (rssi * 2)
        return -120  # Default weak signal
    
    async def _get_network_type(self) -> str:
        """دریافت نوع شبکه"""
        response = await self._send_at_command("AT+COPS?")
        # TODO: Parse network type
        return "4G"  # Default

