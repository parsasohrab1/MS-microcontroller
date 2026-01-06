# راهنمای امنیت ارتباطات

## مقدمه

این راهنما نحوه استفاده از قابلیت‌های امنیت ارتباطات را توضیح می‌دهد.

---

## 1. بهبود رمزنگاری BLE (Firmware)

### استفاده از BLE Security

```c
#include "communication/ble_security.h"

// مقداردهی اولیه
ble_security_init();

// شروع pairing پیشرفته
uint8_t device_address[6] = {0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC};
ble_security_start_pairing(
    BLE_PAIRING_METHOD_NUMERIC_COMPARISON,
    device_address
);

// تکمیل pairing
uint32_t passkey = ble_security_generate_passkey();
ble_security_complete_pairing(device_address, passkey);

// Mutual authentication
ble_security_mutual_authenticate(device_address);

// Key rotation (دوره‌ای)
if (ble_security_needs_key_rotation(device_address)) {
    ble_security_rotate_keys(device_address);
}
```

### تنظیم Security Level

```c
// تنظیم سطح امنیتی بالا
ble_security_set_level(BLE_SECURITY_LEVEL_HIGH);

// دریافت LTK برای encryption
uint8_t ltk[16];
if (ble_security_get_ltk(device_address, ltk)) {
    // استفاده از LTK برای encryption
}
```

---

## 2. Certificate Pinning (Gateway)

### استفاده از Certificate Pinning

```python
from gateway.gateway_service.app.security import (
    init_certificate_pinner,
    get_certificate_pinner
)

# مقداردهی اولیه با pinned certificates
pinned_certs = [
    "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99"
]

pinner = init_certificate_pinner(pinned_certs)

# اضافه کردن certificate از فایل
pinner.add_certificate("/path/to/certificate.pem")

# اضافه کردن certificate از URL
pinner.add_certificate_from_url("https://api.example.com")

# بررسی اتصال
if pinner.verify_connection("api.example.com", 443):
    print("Certificate verified")
else:
    print("Certificate verification failed")
```

### استفاده در HTTP Client

```python
import httpx
from gateway.gateway_service.app.security import get_certificate_pinner

pinner = get_certificate_pinner()

# ایجاد SSL context
ssl_context = pinner.create_ssl_context()

# استفاده در httpx
async with httpx.AsyncClient(verify=ssl_context) as client:
    response = await client.get("https://api.example.com/data")
```

---

## 3. End-to-End Encryption (Gateway)

### استفاده از E2E Encryption

```python
from gateway.gateway_service.app.security import (
    init_e2e_encryption,
    get_e2e_encryption
)

# مقداردهی اولیه
e2e = init_e2e_encryption()

# دریافت public key
public_key_pem = e2e.get_public_key_pem()
print(f"Public Key:\n{public_key_pem}")

# اضافه کردن public key طرف مقابل
peer_id = "patient_123"
e2e.add_peer_public_key(peer_id, peer_public_key_pem)

# تولید session key
encrypted_session_key = e2e.generate_session_key(peer_id)

# ارسال encrypted_session_key به peer
# peer باید آن را با private key خود رمزگشایی کند

# رمزگذاری داده
data = b"Sensitive patient data"
encrypted = e2e.encrypt_data(peer_id, data)

# رمزگشایی داده
decrypted = e2e.decrypt_data(peer_id, encrypted)
```

### رمزگذاری JSON

```python
# رمزگذاری JSON
patient_data = {
    "patient_id": "patient_123",
    "eeg_data": [1.2, 3.4, 5.6],
    "risk_score": 0.85
}

encrypted_json = e2e.encrypt_json(peer_id, patient_data)

# رمزگشایی JSON
decrypted_data = e2e.decrypt_json(peer_id, encrypted_json)
```

### ذخیره و بارگذاری Keys

```python
# ذخیره private key
e2e.save_private_key("/path/to/private_key.pem", password=b"password")

# بارگذاری private key
e2e.load_private_key("/path/to/private_key.pem", password=b"password")
```

---

## بهترین روش‌ها

### 1. BLE Security
- استفاده از pairing method مناسب (Numeric Comparison برای امنیت بالا)
- Key rotation دوره‌ای (هر 1 ساعت)
- Mutual authentication برای همه اتصالات
- استفاده از HSM برای key storage

### 2. Certificate Pinning
- Pin کردن certificates در production
- به‌روزرسانی certificates قبل از expire
- Logging رویدادهای verification failure
- Fallback mechanism برای certificate updates

### 3. End-to-End Encryption
- استفاده از RSA 2048-bit برای key exchange
- استفاده از AES-256-CBC برای data encryption
- Session key rotation دوره‌ای
- Secure storage برای private keys

---

## یکپارچه‌سازی

### در Gateway Service

```python
from gateway.gateway_service.app.security import (
    init_certificate_pinner,
    init_e2e_encryption
)

# Startup
async def startup():
    # Certificate Pinning
    pinned_certs = load_pinned_certificates()
    init_certificate_pinner(pinned_certs)
    
    # E2E Encryption
    e2e = init_e2e_encryption()
    e2e.load_private_key("/path/to/private_key.pem")

# در API endpoints
@app.post("/api/data")
async def receive_data(data: dict):
    e2e = get_e2e_encryption()
    
    # رمزگشایی داده
    decrypted = e2e.decrypt_json("patient_123", data["encrypted_data"])
    
    # پردازش داده
    # ...
```

### در Firmware

```c
// در main loop
void main_loop(void) {
    // بررسی key rotation
    for (int i = 0; i < paired_device_count; i++) {
        if (ble_security_needs_key_rotation(paired_devices[i].device_address)) {
            ble_security_rotate_keys(paired_devices[i].device_address);
        }
    }
    
    // Mutual authentication برای اتصالات جدید
    // ...
}
```

---

**آخرین به‌روزرسانی:** 2024

