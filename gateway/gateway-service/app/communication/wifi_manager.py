"""
Wi-Fi Manager
مدیریت اتصالات Wi-Fi برای انتقال داده‌های حجیم
"""

import asyncio
import socket
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
import subprocess
import platform


@dataclass
class WiFiNetwork:
    """شبکه Wi-Fi"""
    ssid: str
    signal_strength: int  # dBm
    security: str  # WPA2, WPA, Open, etc.
    frequency: int  # MHz (2.4 or 5 GHz)
    connected: bool = False


class WiFiManager:
    """مدیریت Wi-Fi"""
    
    def __init__(self):
        """مقداردهی اولیه"""
        self.connected_devices: Dict[str, socket.socket] = {}
        self.available_networks: List[WiFiNetwork] = []
        self.current_network: Optional[WiFiNetwork] = None
    
    def is_available(self) -> bool:
        """بررسی دسترسی‌پذیری Wi-Fi"""
        try:
            # بررسی اینکه آیا Wi-Fi adapter فعال است
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["netsh", "wlan", "show", "interfaces"],
                    capture_output=True,
                    text=True
                )
                return "State" in result.stdout and "connected" in result.stdout.lower()
            elif platform.system() == "Linux":
                result = subprocess.run(
                    ["iwconfig"],
                    capture_output=True,
                    text=True
                )
                return "IEEE 802.11" in result.stdout
            elif platform.system() == "Darwin":  # macOS
                result = subprocess.run(
                    ["networksetup", "-getairportnetwork", "en0"],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            
            return False
        except Exception as e:
            logger.error(f"Error checking WiFi availability: {e}")
            return False
    
    def get_signal_strength(self) -> float:
        """دریافت قدرت سیگنال Wi-Fi (0-1)"""
        if not self.current_network:
            return 0.0
        
        # تبدیل dBm به 0-1 scale
        # -30 dBm = 1.0, -90 dBm = 0.0
        dbm = self.current_network.signal_strength
        normalized = (dbm + 90) / 60  # -30 to -90 range
        return max(0.0, min(1.0, normalized))
    
    async def scan_networks(self) -> List[WiFiNetwork]:
        """اسکن شبکه‌های Wi-Fi"""
        networks = []
        
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["netsh", "wlan", "show", "networks", "mode=Bssid"],
                    capture_output=True,
                    text=True
                )
                # Parse output
                # TODO: Parse Windows output
            elif platform.system() == "Linux":
                result = subprocess.run(
                    ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,FREQ", "device", "wifi", "list"],
                    capture_output=True,
                    text=True
                )
                # Parse output
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(':')
                        if len(parts) >= 4:
                            networks.append(WiFiNetwork(
                                ssid=parts[0],
                                signal_strength=int(parts[1]),
                                security=parts[2],
                                frequency=int(parts[3]) if parts[3].isdigit() else 2400
                            ))
            
            self.available_networks = networks
            return networks
        
        except Exception as e:
            logger.error(f"Error scanning WiFi networks: {e}")
            return []
    
    async def connect(
        self,
        device_id: str,
        ssid: Optional[str] = None,
        password: Optional[str] = None
    ) -> bool:
        """
        اتصال به شبکه Wi-Fi
        
        Args:
            device_id: شناسه دستگاه (برای ارتباط مستقیم)
            ssid: نام شبکه (اختیاری - برای اتصال به شبکه)
            password: رمز شبکه (اختیاری)
        
        Returns:
            True در صورت موفقیت
        """
        try:
            # اگر SSID ارائه شده، به شبکه Wi-Fi متصل می‌شویم
            if ssid:
                return await self._connect_to_network(ssid, password)
            
            # در غیر این صورت، ارتباط مستقیم با دستگاه
            # (مثلاً Wi-Fi Direct یا Access Point mode)
            return await self._connect_to_device(device_id)
        
        except Exception as e:
            logger.error(f"WiFi connection error: {e}")
            return False
    
    async def _connect_to_network(self, ssid: str, password: Optional[str]) -> bool:
        """اتصال به شبکه Wi-Fi"""
        try:
            if platform.system() == "Windows":
                if password:
                    cmd = ["netsh", "wlan", "connect", f"name={ssid}", f"ssid={ssid}", f"key={password}"]
                else:
                    cmd = ["netsh", "wlan", "connect", f"name={ssid}"]
                result = subprocess.run(cmd, capture_output=True, text=True)
            elif platform.system() == "Linux":
                if password:
                    cmd = ["nmcli", "device", "wifi", "connect", ssid, "password", password]
                else:
                    cmd = ["nmcli", "device", "wifi", "connect", ssid]
                result = subprocess.run(cmd, capture_output=True, text=True)
            else:
                return False
            
            if result.returncode == 0:
                # پیدا کردن شبکه در لیست
                for network in self.available_networks:
                    if network.ssid == ssid:
                        network.connected = True
                        self.current_network = network
                        logger.info(f"Connected to WiFi network: {ssid}")
                        return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error connecting to network: {e}")
            return False
    
    async def _connect_to_device(self, device_id: str) -> bool:
        """اتصال مستقیم به دستگاه (Wi-Fi Direct)"""
        try:
            # ایجاد socket برای ارتباط
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            
            # TODO: دریافت IP دستگاه از discovery
            device_ip = await self._discover_device(device_id)
            if not device_ip:
                return False
            
            # اتصال
            sock.connect((device_ip, 8080))  # Port پیش‌فرض
            self.connected_devices[device_id] = sock
            
            logger.info(f"Connected to device {device_id} via WiFi")
            return True
        
        except Exception as e:
            logger.error(f"Error connecting to device: {e}")
            return False
    
    async def _discover_device(self, device_id: str) -> Optional[str]:
        """کشف دستگاه در شبکه"""
        # TODO: پیاده‌سازی discovery (mDNS, SSDP, etc.)
        return None
    
    async def disconnect(self, device_id: str) -> bool:
        """قطع اتصال"""
        if device_id in self.connected_devices:
            sock = self.connected_devices[device_id]
            sock.close()
            del self.connected_devices[device_id]
            return True
        return False
    
    async def send_data(self, device_id: str, data: bytes, priority: int = 0) -> bool:
        """ارسال داده"""
        if device_id not in self.connected_devices:
            return False
        
        try:
            sock = self.connected_devices[device_id]
            # اضافه کردن header (priority, length)
            header = f"{priority:02d}{len(data):08d}".encode()
            sock.sendall(header + data)
            return True
        except Exception as e:
            logger.error(f"Error sending data: {e}")
            return False
    
    async def receive_data(self, device_id: str, timeout: float = 5.0) -> Optional[bytes]:
        """دریافت داده"""
        if device_id not in self.connected_devices:
            return None
        
        try:
            sock = self.connected_devices[device_id]
            sock.settimeout(timeout)
            
            # دریافت header
            header = sock.recv(10)
            if len(header) < 10:
                return None
            
            priority = int(header[:2])
            length = int(header[2:])
            
            # دریافت داده
            data = b''
            while len(data) < length:
                chunk = sock.recv(length - len(data))
                if not chunk:
                    return None
                data += chunk
            
            return data
        
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"Error receiving data: {e}")
            return None
    
    def get_bandwidth(self) -> float:
        """دریافت bandwidth تخمینی (Mbps)"""
        if not self.current_network:
            return 0.0
        
        # تخمین بر اساس frequency و signal strength
        if self.current_network.frequency >= 5000:  # 5 GHz
            base_bandwidth = 100.0  # Mbps
        else:  # 2.4 GHz
            base_bandwidth = 50.0  # Mbps
        
        # کاهش بر اساس signal strength
        signal_factor = self.get_signal_strength()
        return base_bandwidth * signal_factor

