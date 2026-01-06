"""
NFC Manager
مدیریت NFC برای pairing سریع
"""

import asyncio
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
import json
import base64


@dataclass
class NFCDevice:
    """دستگاه NFC"""
    device_id: str
    paired_at: datetime
    pairing_token: str
    metadata: Dict


class NFCManager:
    """مدیریت NFC"""
    
    def __init__(self):
        """مقداردهی اولیه"""
        self.paired_devices: Dict[str, NFCDevice] = {}
        self.pairing_mode = False
    
    async def pair(self, device_id: str) -> bool:
        """
        Pairing با دستگاه از طریق NFC
        
        Args:
            device_id: شناسه دستگاه
        
        Returns:
            True در صورت موفقیت
        """
        try:
            # شبیه‌سازی pairing
            # در واقعیت، از کتابخانه NFC استفاده می‌شود
            # (مثلاً nfcpy برای Python)
            
            # خواندن داده از NFC tag
            nfc_data = await self._read_nfc_tag()
            
            if not nfc_data:
                logger.error("Failed to read NFC tag")
                return False
            
            # Parse داده
            device_info = json.loads(nfc_data)
            
            # ذخیره اطلاعات pairing
            pairing_token = self._generate_pairing_token()
            
            self.paired_devices[device_id] = NFCDevice(
                device_id=device_id,
                paired_at=datetime.now(),
                pairing_token=pairing_token,
                metadata=device_info
            )
            
            logger.info(f"Paired with device {device_id} via NFC")
            return True
        
        except Exception as e:
            logger.error(f"NFC pairing error: {e}")
            return False
    
    async def write_pairing_info(self, device_id: str, pairing_data: Dict) -> bool:
        """
        نوشتن اطلاعات pairing روی NFC tag
        
        Args:
            device_id: شناسه دستگاه
            pairing_data: داده‌های pairing
        
        Returns:
            True در صورت موفقیت
        """
        try:
            # آماده‌سازی داده
            data = {
                "device_id": device_id,
                "pairing_token": self._generate_pairing_token(),
                "timestamp": datetime.now().isoformat(),
                **pairing_data
            }
            
            json_data = json.dumps(data)
            
            # نوشتن روی NFC tag
            success = await self._write_nfc_tag(json_data)
            
            if success:
                logger.info(f"Wrote pairing info to NFC tag for {device_id}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error writing NFC tag: {e}")
            return False
    
    async def send_data(self, device_id: str, data: bytes) -> bool:
        """
        ارسال داده از طریق NFC (برای داده‌های کوچک)
        
        Args:
            device_id: شناسه دستگاه
            data: داده (حداکثر چند KB)
        
        Returns:
            True در صورت موفقیت
        """
        if device_id not in self.paired_devices:
            logger.error(f"Device {device_id} not paired")
            return False
        
        if len(data) > 4096:  # محدودیت NFC
            logger.warning("Data too large for NFC, use another protocol")
            return False
        
        try:
            # تبدیل به base64 برای انتقال
            encoded_data = base64.b64encode(data).decode('utf-8')
            
            # نوشتن روی NFC tag
            success = await self._write_nfc_tag(encoded_data)
            
            return success
        
        except Exception as e:
            logger.error(f"Error sending data via NFC: {e}")
            return False
    
    async def disconnect(self, device_id: str) -> bool:
        """قطع pairing"""
        if device_id in self.paired_devices:
            del self.paired_devices[device_id]
            return True
        return False
    
    def get_paired_device(self, device_id: str) -> Optional[NFCDevice]:
        """دریافت اطلاعات دستگاه paired"""
        return self.paired_devices.get(device_id)
    
    def _generate_pairing_token(self) -> str:
        """تولید token برای pairing"""
        import secrets
        return secrets.token_urlsafe(32)
    
    async def _read_nfc_tag(self) -> Optional[str]:
        """
        خواندن از NFC tag
        
        Note: این یک شبیه‌سازی است
        در واقعیت، از کتابخانه NFC استفاده می‌شود
        """
        # TODO: پیاده‌سازی واقعی با nfcpy یا مشابه
        # مثال:
        # import nfc
        # clf = nfc.ContactlessFrontend('usb')
        # tag = clf.connect(rdwr={'on-connect': lambda tag: False})
        # return tag.ndef.message if tag.ndef else None
        
        # شبیه‌سازی
        await asyncio.sleep(0.1)
        return json.dumps({
            "device_id": "device_123",
            "device_name": "MS-Device",
            "ble_address": "AA:BB:CC:DD:EE:FF"
        })
    
    async def _write_nfc_tag(self, data: str) -> bool:
        """
        نوشتن روی NFC tag
        
        Note: این یک شبیه‌سازی است
        """
        # TODO: پیاده‌سازی واقعی
        # مثال:
        # import nfc
        # clf = nfc.ContactlessFrontend('usb')
        # tag = clf.connect(rdwr={'on-connect': lambda tag: False})
        # if tag.ndef:
        #     tag.ndef.message = nfc.ndef.Message(data)
        #     return True
        # return False
        
        # شبیه‌سازی
        await asyncio.sleep(0.1)
        return True

