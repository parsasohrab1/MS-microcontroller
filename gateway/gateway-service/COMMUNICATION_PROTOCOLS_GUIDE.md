# راهنمای پروتکل‌های ارتباطی

## مقدمه

این راهنما نحوه استفاده از پروتکل‌های ارتباطی مختلف (BLE, Wi-Fi, Cellular, NFC) را توضیح می‌دهد.

---

## 1. Protocol Manager

### استفاده پایه

```python
from app.communication import get_protocol_manager, ProtocolType

manager = get_protocol_manager()

# اتصال با BLE
await manager.connect(ProtocolType.BLE, "AA:BB:CC:DD:EE:FF")

# اتصال با Wi-Fi
await manager.connect(
    ProtocolType.WIFI,
    "device_123",
    config={"ssid": "MyNetwork", "password": "mypass"}
)

# انتخاب خودکار بهترین پروتکل
best_protocol = manager.select_best_protocol("device_123")
await manager.connect(best_protocol, "device_123")
```

### ارسال داده

```python
# ارسال داده
data = b"Hello, device!"
success = await manager.send_data("device_123", data, priority=1)

# دریافت داده
received = await manager.receive_data("device_123", timeout=5.0)
```

### تغییر خودکار پروتکل

```python
# تغییر خودکار در صورت نیاز
await manager.auto_switch_protocol("device_123")
```

---

## 2. Wi-Fi Manager

### اسکن شبکه‌ها

```python
from app.communication import WiFiManager

wifi = WiFiManager()

# اسکن شبکه‌های موجود
networks = await wifi.scan_networks()
for network in networks:
    print(f"{network.ssid}: {network.signal_strength} dBm")
```

### اتصال به شبکه

```python
# اتصال به شبکه Wi-Fi
success = await wifi.connect(
    "device_123",
    ssid="MyNetwork",
    password="mypass"
)

# بررسی قدرت سیگنال
signal = wifi.get_signal_strength()
print(f"Signal strength: {signal * 100}%")
```

### ارسال/دریافت داده

```python
# ارسال داده حجیم
large_data = b"..." * 1000
success = await wifi.send_data("device_123", large_data, priority=2)

# دریافت داده
data = await wifi.receive_data("device_123", timeout=10.0)
```

---

## 3. Cellular Manager

### اتصال Cellular

```python
from app.communication import CellularManager

cellular = CellularManager()

# بررسی دسترسی
if cellular.is_available():
    # اتصال
    success = await cellular.connect("device_123", apn="internet")
    
    # بررسی قدرت سیگنال
    signal = cellular.get_signal_strength()
    print(f"Cellular signal: {signal * 100}%")
```

### ارسال داده

```python
# ارسال داده از طریق Cellular
data = b"Emergency data"
success = await cellular.send_data("device_123", data, priority=2)
```

---

## 4. NFC Manager

### Pairing سریع

```python
from app.communication import NFCManager

nfc = NFCManager()

# Pairing با دستگاه
success = await nfc.pair("device_123")

# نوشتن اطلاعات pairing روی tag
await nfc.write_pairing_info("device_123", {
    "device_name": "MS-Device",
    "ble_address": "AA:BB:CC:DD:EE:FF"
})
```

### ارسال داده کوچک

```python
# ارسال داده کوچک (حداکثر 4KB)
small_data = b"Pairing token"
success = await nfc.send_data("device_123", small_data)
```

---

## 5. انتخاب پروتکل مناسب

### بر اساس نوع داده

```python
def select_protocol_for_data(data_size: int, priority: int) -> ProtocolType:
    """انتخاب پروتکل بر اساس اندازه داده و اولویت"""
    
    # داده‌های کوچک و بحرانی: NFC
    if data_size < 4096 and priority >= 2:
        return ProtocolType.NFC
    
    # داده‌های حجیم: Wi-Fi
    if data_size > 100000:  # > 100 KB
        return ProtocolType.WIFI
    
    # داده‌های متوسط: BLE
    if data_size < 100000:
        return ProtocolType.BLE
    
    # مناطق دور: Cellular
    return ProtocolType.CELLULAR
```

### بر اساس شرایط شبکه

```python
manager = get_protocol_manager()

# بررسی دسترسی‌پذیری
if wifi_manager.is_available() and wifi_manager.get_signal_strength() > 0.5:
    protocol = ProtocolType.WIFI
elif cellular_manager.is_available():
    protocol = ProtocolType.CELLULAR
else:
    protocol = ProtocolType.BLE  # Fallback
```

---

## بهترین روش‌ها

### 1. Fallback Strategy
```python
protocols = [ProtocolType.WIFI, ProtocolType.CELLULAR, ProtocolType.BLE]

for protocol in protocols:
    if await manager.connect(protocol, device_id):
        break
```

### 2. Bandwidth Management
```python
# استفاده از Wi-Fi برای داده‌های حجیم
if data_size > 100000:
    await manager.connect(ProtocolType.WIFI, device_id)
```

### 3. Energy Efficiency
```python
# استفاده از BLE برای داده‌های کوچک و مکرر
if data_size < 1000 and frequency == "high":
    await manager.connect(ProtocolType.BLE, device_id)
```

---

## منابع

- [BLE Specification](https://www.bluetooth.com/specifications/)
- [Wi-Fi Standards](https://www.wi-fi.org/)
- [Cellular Standards](https://www.3gpp.org/)
- [NFC Forum](https://nfc-forum.org/)

---

**آخرین به‌روزرسانی:** 2024

