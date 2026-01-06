# راهنمای بهبودهای Gateway

## مقدمه

این راهنما نحوه استفاده از بهبودهای مدیریت اتصال BLE را توضیح می‌دهد.

---

## 1. Connection Pooling

### استفاده پایه

```python
from app.ble import get_connection_pool
from bleak import BleakClient

# دریافت connection pool
pool = get_connection_pool()

# دریافت اتصال
client = await pool.get_connection(
    device_address="AA:BB:CC:DD:EE:FF",
    device_name="MS-Device"
)

if client:
    # استفاده از client
    services = await client.get_services()
    
    # آزاد کردن اتصال (بازگشت به pool)
    await pool.release_connection("AA:BB:CC:DD:EE:FF")
```

### پیکربندی

```python
from app.ble.connection_pool import BLEConnectionPool

# ایجاد pool با تنظیمات سفارشی
pool = BLEConnectionPool(
    max_connections=20,
    connection_timeout=15.0,
    idle_timeout=600.0,  # 10 minutes
    max_retries=5,
    retry_delay=2.0
)
```

### آمار Pool

```python
stats = pool.get_pool_stats()
print(f"Connected: {stats['connected']}")
print(f"Total: {stats['total_connections']}")
```

---

## 2. Auto-Reconnection

### استفاده پایه

```python
from app.ble import get_reconnect_manager, get_connection_pool

pool = get_connection_pool()
reconnect_manager = get_reconnect_manager()

async def reconnect_callback(device_address: str) -> bool:
    """Callback برای اتصال مجدد"""
    client = await pool.get_connection(device_address)
    return client is not None and client.is_connected

# ثبت دستگاه برای auto-reconnect
reconnect_manager.register_device(
    device_address="AA:BB:CC:DD:EE:FF",
    reconnect_callback=reconnect_callback,
    auto_start=True
)
```

### استراتژی‌های اتصال مجدد

```python
from app.ble.auto_reconnect import AutoReconnectManager, ReconnectStrategy

# Exponential backoff (پیش‌فرض)
manager = AutoReconnectManager(
    max_reconnect_attempts=10,
    initial_delay=1.0,
    max_delay=60.0,
    strategy=ReconnectStrategy.EXPONENTIAL_BACKOFF
)

# Fixed interval
manager = AutoReconnectManager(
    strategy=ReconnectStrategy.FIXED_INTERVAL,
    initial_delay=5.0
)

# Custom delays
manager = AutoReconnectManager(
    strategy=ReconnectStrategy.CUSTOM,
    custom_delays=[1.0, 2.0, 5.0, 10.0, 30.0]
)
```

### استفاده در FastAPI

```python
from fastapi import FastAPI, BackgroundTasks
from app.ble import get_reconnect_manager, get_connection_pool

app = FastAPI()
pool = get_connection_pool()
reconnect_manager = get_reconnect_manager()

@app.on_event("startup")
async def startup():
    # ثبت دستگاه‌های شناخته شده
    devices = ["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"]
    
    async def reconnect(addr):
        client = await pool.get_connection(addr)
        return client is not None
    
    for device in devices:
        reconnect_manager.register_device(device, reconnect)

@app.on_event("shutdown")
async def shutdown():
    # توقف تمام reconnect tasks
    for device in reconnect_manager._reconnect_tasks.keys():
        reconnect_manager.stop_reconnect(device)
```

---

## 3. Data Compression

### استفاده پایه

```python
from app.ble import get_compressor, CompressionAlgorithm

# دریافت compressor
compressor = get_compressor(CompressionAlgorithm.ZLIB)

# فشرده‌سازی
data = {"sensor_value": 42.5, "timestamp": "2024-01-01T12:00:00"}
compressed = compressor.compress(data)
print(f"Original: {len(str(data))} bytes")
print(f"Compressed: {len(compressed)} bytes")

# از حالت فشرده خارج کردن
decompressed = compressor.decompress(compressed)
print(decompressed)
```

### استفاده با Base64

```python
# برای انتقال در text format
compressed_b64 = compressor.compress_base64(data)
print(f"Base64: {compressed_b64}")

# از base64 خارج کردن
decompressed = compressor.decompress_base64(compressed_b64)
```

### مقایسه الگوریتم‌ها

```python
data = {"sensor_values": list(range(1000))}
original_size = len(str(data).encode('utf-8'))

for algo in CompressionAlgorithm:
    if algo == CompressionAlgorithm.NONE:
        continue
    
    compressor = get_compressor(algo)
    compressed = compressor.compress(data)
    ratio = compressor.get_compression_ratio(
        str(data).encode('utf-8'),
        compressed
    )
    
    print(f"{algo.value}: {len(compressed)} bytes ({ratio*100:.1f}%)")
```

---

## 4. Bandwidth Optimization

### استفاده پایه

```python
from app.ble import get_bandwidth_optimizer

optimizer = get_bandwidth_optimizer()

# اضافه کردن داده به صف
optimizer.enqueue(
    data={"sensor": "temperature", "value": 25.5},
    priority=0  # normal
)

# داده با اولویت بالا
optimizer.enqueue(
    data={"alert": "critical", "message": "..."},
    priority=2  # critical
)
```

### پیکربندی

```python
from app.ble.bandwidth_optimizer import BandwidthOptimizer
from app.ble.data_compression import CompressionAlgorithm

optimizer = BandwidthOptimizer(
    max_queue_size=200,
    batch_size=20,
    batch_timeout=2.0,
    compression_enabled=True,
    compression_algorithm=CompressionAlgorithm.ZLIB,
    priority_queue=True
)
```

### یکپارچه‌سازی با ارسال داده

```python
async def send_data_to_server(data):
    """ارسال داده به سرور"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.example.com/data",
            json=data
        ) as response:
            return await response.json()

# استفاده از optimizer
optimizer = get_bandwidth_optimizer()

# اضافه کردن داده
optimizer.enqueue({"sensor": "eeg", "data": [...]})

# پردازش batch (در background task)
async def process_batches():
    while True:
        batch = await optimizer._collect_batch()
        if batch:
            data = [p.data for p in batch]
            await send_data_to_server(data)
        await asyncio.sleep(1)
```

---

## 5. استفاده ترکیبی

### مثال کامل

```python
import asyncio
from app.ble import (
    get_connection_pool,
    get_reconnect_manager,
    get_compressor,
    get_bandwidth_optimizer,
    CompressionAlgorithm
)

# دریافت instances
pool = get_connection_pool()
reconnect_manager = get_reconnect_manager()
compressor = get_compressor(CompressionAlgorithm.ZLIB)
optimizer = get_bandwidth_optimizer()

async def read_sensor_data(device_address: str):
    """خواندن داده از سنسور"""
    # دریافت اتصال از pool
    client = await pool.get_connection(device_address)
    
    if not client or not client.is_connected:
        # شروع auto-reconnect
        reconnect_manager.start_reconnect(device_address)
        return None
    
    try:
        # خواندن داده
        data = await client.read_gatt_char("00002a00-0000-1000-8000-00805f9b34fb")
        
        # فشرده‌سازی
        compressed = compressor.compress(data)
        
        # اضافه به optimizer
        optimizer.enqueue(compressed, priority=0)
        
        return data
    
    except Exception as e:
        logger.error(f"Error reading data: {e}")
        # در صورت خطا، اتصال مجدد
        reconnect_manager.start_reconnect(device_address)
        return None
    
    finally:
        # آزاد کردن اتصال
        await pool.release_connection(device_address)

# استفاده
asyncio.run(read_sensor_data("AA:BB:CC:DD:EE:FF"))
```

---

## 6. Edge Computing (راهنمای طراحی)

### مفهوم

Edge Computing به معنای پردازش داده‌ها در Gateway (edge) به جای ارسال به سرور است.

### مزایا

1. **کاهش Latency**: پردازش محلی سریع‌تر است
2. **کاهش Bandwidth**: فقط نتایج ارسال می‌شود
3. **کار Offline**: حتی بدون اتصال به سرور کار می‌کند
4. **Privacy**: داده‌های خام در Gateway باقی می‌ماند

### معماری پیشنهادی

```
┌─────────────┐
│   Device    │
│  (BLE)      │
└──────┬──────┘
       │
┌──────▼──────────────────┐
│      Gateway            │
│  ┌──────────────────┐   │
│  │  Data Collection │   │
│  └────────┬─────────┘   │
│           │             │
│  ┌────────▼─────────┐   │
│  │  Edge Processing │   │
│  │  - Filtering     │   │
│  │  - Aggregation   │   │
│  │  - ML Inference  │   │
│  └────────┬─────────┘   │
│           │             │
│  ┌────────▼─────────┐   │
│  │  Local Storage   │   │
│  │  (SQLite/Redis)  │   │
│  └────────┬─────────┘   │
│           │             │
└───────────┼─────────────┘
            │
    ┌───────▼────────┐
    │   Cloud API    │
    │  (Results Only)│
    └────────────────┘
```

### پیاده‌سازی

```python
# edge_processor.py
class EdgeProcessor:
    """پردازشگر Edge"""
    
    def __init__(self):
        self.local_storage = LocalStorage()
        self.ml_model = load_ml_model()
    
    async def process_sensor_data(self, data: dict):
        """پردازش داده سنسور"""
        # 1. فیلتر کردن
        filtered = self.filter_data(data)
        
        # 2. تجمیع
        aggregated = self.aggregate_data(filtered)
        
        # 3. ML Inference
        prediction = self.ml_model.predict(aggregated)
        
        # 4. ذخیره محلی
        await self.local_storage.save(aggregated, prediction)
        
        # 5. ارسال فقط نتایج به سرور
        if prediction["risk_level"] > 0.7:
            await self.send_to_cloud({
                "prediction": prediction,
                "timestamp": datetime.now().isoformat()
            })
        
        return prediction
```

---

## بهترین روش‌ها

### 1. Connection Management
- استفاده از connection pool برای اتصالات مکرر
- بستن اتصالات idle
- مدیریت خطاها

### 2. Reconnection
- استفاده از exponential backoff
- محدود کردن تعداد تلاش‌ها
- لاگ کردن خطاها

### 3. Compression
- انتخاب الگوریتم مناسب (ZLIB برای تعادل)
- فشرده‌سازی فقط برای داده‌های بزرگ
- اندازه‌گیری نسبت فشرده‌سازی

### 4. Bandwidth
- استفاده از batching
- اولویت‌بندی داده‌ها
- حذف داده‌های قدیمی در صورت پر شدن صف

---

## منابع

- [Bleak Documentation](https://bleak.readthedocs.io/)
- [BLE Best Practices](https://www.bluetooth.com/learn-about-bluetooth/tech-overview/)
- [Data Compression Algorithms](https://en.wikipedia.org/wiki/Data_compression)

---

**آخرین به‌روزرسانی:** 2024

