# راهنمای استفاده از Message Queue (RabbitMQ)

## مقدمه

این راهنما نحوه استفاده از Message Queue برای ارتباط ناهمزمان بین سرویس‌ها را توضیح می‌دهد.

---

## نصب و راه‌اندازی

### 1. نصب RabbitMQ

```bash
# با Docker
docker run -d --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=admin \
  -e RABBITMQ_DEFAULT_PASS=admin \
  rabbitmq:3-management-alpine

# یا با docker-compose (از فایل اصلی)
docker-compose up -d rabbitmq
```

### 2. نصب وابستگی‌ها

```bash
pip install pika>=1.3.2
```

### 3. تنظیم متغیر محیطی

```bash
export RABBITMQ_URL=amqp://admin:admin@localhost:5672/
```

---

## استفاده پایه

### مثال 1: ارسال پیام ساده

```python
from shared.message_queue import get_rabbitmq_client

# دریافت کلاینت
mq = get_rabbitmq_client()

# ارسال پیام
message = {
    "user_id": 123,
    "action": "data_received",
    "timestamp": "2024-01-01T12:00:00",
    "data": {"sensor_value": 42.5}
}

mq.publish_message(
    queue_name="sensor_data",
    message=message,
    persistent=True
)
```

### مثال 2: دریافت و پردازش پیام

```python
from shared.message_queue import get_rabbitmq_client

mq = get_rabbitmq_client()

def process_sensor_data(message: dict, delivery_tag: int) -> bool:
    """پردازش داده سنسور"""
    try:
        user_id = message.get("user_id")
        data = message.get("data")
        
        # پردازش...
        print(f"Processing data for user {user_id}: {data}")
        
        # در صورت موفقیت
        return True
    except Exception as e:
        print(f"Error processing message: {e}")
        # در صورت خطا، پیام دوباره در صف قرار می‌گیرد
        return False

# شروع مصرف
mq.consume_messages(
    queue_name="sensor_data",
    callback=process_sensor_data,
    auto_ack=False,
    prefetch_count=1
)
```

---

## استفاده پیشرفته

### مثال 3: استفاده از Exchange و Routing

```python
from shared.message_queue import get_rabbitmq_client

mq = get_rabbitmq_client()

# تعریف exchange
mq.declare_exchange("sensor_events", exchange_type="topic")

# تعریف صف‌ها
mq.declare_queue("sensor_data_processing")
mq.declare_queue("sensor_data_storage")

# اتصال صف‌ها به exchange
mq.bind_queue("sensor_data_processing", "sensor_events", "sensor.data.*")
mq.bind_queue("sensor_data_storage", "sensor_events", "sensor.data.*")

# ارسال پیام با routing key
mq.publish_to_exchange(
    exchange_name="sensor_events",
    routing_key="sensor.data.eeg",
    message={
        "type": "eeg",
        "data": [1.2, 3.4, 5.6]
    }
)
```

### مثال 4: استفاده در FastAPI Service

```python
from fastapi import FastAPI, BackgroundTasks
from shared.message_queue import get_rabbitmq_client

app = FastAPI()
mq = get_rabbitmq_client()

@app.post("/data/sensor")
async def receive_sensor_data(data: dict, background_tasks: BackgroundTasks):
    """دریافت داده سنسور و ارسال به queue"""
    
    # ارسال به queue برای پردازش ناهمزمان
    background_tasks.add_task(
        send_to_queue,
        queue_name="sensor_data",
        message=data
    )
    
    return {"status": "received", "queued": True}

def send_to_queue(queue_name: str, message: dict):
    """ارسال به queue"""
    mq.publish_message(queue_name, message)
```

### مثال 5: Worker Service

```python
# worker.py
from shared.message_queue import get_rabbitmq_client
import signal
import sys

mq = get_rabbitmq_client()

def signal_handler(sig, frame):
    """Handler برای graceful shutdown"""
    print("\nShutting down...")
    mq.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def process_message(message: dict, delivery_tag: int) -> bool:
    """پردازش پیام"""
    print(f"Processing: {message}")
    # پردازش...
    return True

if __name__ == "__main__":
    print("Starting worker...")
    mq.consume_messages(
        queue_name="sensor_data",
        callback=process_message,
        auto_ack=False
    )
```

---

## الگوهای استفاده

### 1. Work Queue Pattern

برای توزیع کار بین چند worker:

```python
# Producer
mq.publish_message("tasks", {"task_id": 1, "data": "..."})

# Worker 1, 2, 3...
mq.consume_messages("tasks", process_task)
```

### 2. Pub/Sub Pattern

برای broadcast پیام‌ها:

```python
# Publisher
mq.declare_exchange("events", "fanout")
mq.publish_to_exchange("events", "", {"event": "user_created"})

# Subscriber 1, 2, 3...
mq.declare_queue("user_service_queue")
mq.bind_queue("user_service_queue", "events", "")
mq.consume_messages("user_service_queue", handle_event)
```

### 3. Routing Pattern

برای routing انتخابی:

```python
# Publisher
mq.declare_exchange("logs", "direct")
mq.publish_to_exchange("logs", "error", {"level": "error", "message": "..."})
mq.publish_to_exchange("logs", "info", {"level": "info", "message": "..."})

# Consumer
mq.declare_queue("error_logs")
mq.bind_queue("error_logs", "logs", "error")
mq.consume_messages("error_logs", handle_error)
```

### 4. Topic Pattern

برای routing پیچیده‌تر:

```python
# Publisher
mq.declare_exchange("sensor_events", "topic")
mq.publish_to_exchange("sensor_events", "sensor.eeg.data", {...})
mq.publish_to_exchange("sensor_events", "sensor.biomarker.data", {...})

# Consumer
mq.declare_queue("eeg_processor")
mq.bind_queue("eeg_processor", "sensor_events", "sensor.eeg.*")
mq.consume_messages("eeg_processor", process_eeg)
```

---

## بهترین روش‌ها

### 1. Error Handling

```python
def process_message(message: dict, delivery_tag: int) -> bool:
    try:
        # پردازش
        return True
    except RetryableError:
        # خطای قابل retry
        return False  # پیام دوباره در صف قرار می‌گیرد
    except NonRetryableError:
        # خطای غیرقابل retry
        # لاگ و acknowledge
        logger.error(f"Non-retryable error: {e}")
        return True  # پیام acknowledge می‌شود
```

### 2. Idempotency

```python
def process_message(message: dict, delivery_tag: int) -> bool:
    message_id = message.get("id")
    
    # بررسی اینکه آیا قبلاً پردازش شده
    if is_already_processed(message_id):
        return True  # Acknowledge بدون پردازش
    
    # پردازش
    process(message)
    
    # علامت‌گذاری به عنوان پردازش شده
    mark_as_processed(message_id)
    
    return True
```

### 3. Dead Letter Queue

```python
# تعریف DLQ
mq.declare_queue("sensor_data_dlq")

# در صورت خطاهای مکرر، پیام به DLQ ارسال می‌شود
# (نیاز به پیکربندی در RabbitMQ)
```

---

## مانیتورینگ

### Management UI

دسترسی به Management UI:
```
http://localhost:15672
Username: admin
Password: admin
```

### Metrics

```python
# بررسی تعداد پیام‌های در صف
# (نیاز به استفاده از Management API)
```

---

## منابع

- [RabbitMQ Tutorials](https://www.rabbitmq.com/getstarted.html)
- [Pika Documentation](https://pika.readthedocs.io/)
- [RabbitMQ Best Practices](https://www.rabbitmq.com/best-practices.html)

---

**آخرین به‌روزرسانی:** 2024

