"""
Communication Module
ماژول ارتباطات
"""

from .protocol_manager import ProtocolManager, ProtocolType, get_protocol_manager
from .wifi_manager import WiFiManager
from .cellular_manager import CellularManager
from .nfc_manager import NFCManager

__all__ = [
    "ProtocolManager",
    "ProtocolType",
    "get_protocol_manager",
    "WiFiManager",
    "CellularManager",
    "NFCManager",
]

