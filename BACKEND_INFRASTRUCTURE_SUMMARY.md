# خلاصه زیرساخت Backend

## ✅ وضعیت پیاده‌سازی

### 1. Message Queue (RabbitMQ) ✅

**فایل‌ها:**
- `cloud/services/shared/message_queue.py` - کلاینت RabbitMQ
- `cloud/services/MESSAGE_QUEUE_GUIDE.md` - راهنمای استفاده
- `cloud/docker-compose.yml` - شامل RabbitMQ service

**قابلیت‌ها:**
- ✅ Work Queue Pattern
- ✅ Pub/Sub Pattern
- ✅ Routing Pattern
- ✅ Topic Pattern
- ✅ Persistent messages
- ✅ Auto-reconnection
- ✅ Retry mechanism

**استفاده:**
```python
from shared.message_queue import get_rabbitmq_client

mq = get_rabbitmq_client()
mq.publish_message("sensor_data", {"value": 42.5})
```

---

### 2. Redis Caching ✅

**فایل‌ها:**
- `cloud/services/shared/redis_client.py` - کلاینت Redis
- `cloud/services/REDIS_CACHING_GUIDE.md` - راهنمای استفاده
- `cloud/docker-compose.yml` - شامل Redis service

**قابلیت‌ها:**
- ✅ Cache operations (set/get/delete)
- ✅ Session management
- ✅ Rate limiting
- ✅ Real-time analytics
- ✅ TTL support
- ✅ JSON serialization

**استفاده:**
```python
from shared.redis_client import get_redis_client

redis = get_redis_client()
redis.set_cache("user:123", {"name": "John"}, ttl=3600)
user = redis.get_cache("user:123")
```

---

### 3. CI/CD Pipeline ✅

**فایل‌ها:**
- `.github/workflows/ci.yml` - CI Pipeline
- `.github/workflows/deploy.yml` - Deployment Pipeline
- `infrastructure/terraform/main.tf` - Infrastructure as Code
- `infrastructure/ansible/deploy-staging.yml` - Ansible playbook

**قابلیت‌ها:**
- ✅ Automated Testing (Unit, Integration, E2E, Performance, Security)
- ✅ Automated Deployment (Staging, Production)
- ✅ Blue-Green Deployment
- ✅ Rollback mechanism
- ✅ Docker image builds
- ✅ Infrastructure as Code (Terraform + Ansible)

**اجرا:**
```bash
# CI به صورت خودکار در Push/PR اجرا می‌شود
# Manual deployment
gh workflow run deploy.yml -f environment=production
```

---

### 4. Centralized Logging (ELK Stack) ✅

**فایل‌ها:**
- `cloud/services/shared/logging_config.py` - پیکربندی Logging
- `infrastructure/monitoring/docker-compose.monitoring.yml` - ELK Stack
- `infrastructure/monitoring/prometheus/prometheus.yml` - Prometheus config

**قابلیت‌ها:**
- ✅ ELK Stack (Elasticsearch, Logstash, Kibana)
- ✅ Centralized logging
- ✅ Log aggregation
- ✅ Prometheus + Grafana (APM)
- ✅ Sentry (Error Tracking)

**راه‌اندازی:**
```bash
docker-compose -f infrastructure/monitoring/docker-compose.monitoring.yml up -d
```

**استفاده:**
```python
from shared.logging_config import setup_logging

setup_logging(
    service_name="user-management",
    environment="production",
    log_level="INFO",
    elk_enabled=True
)
```

---

## 📊 ماتریس وضعیت

| کامپوننت | وضعیت | فایل‌ها | مستندات | تست |
|----------|-------|---------|----------|-----|
| Message Queue | ✅ کامل | ✅ | ✅ | ⏳ |
| Redis Caching | ✅ کامل | ✅ | ✅ | ⏳ |
| CI/CD Pipeline | ✅ کامل | ✅ | ✅ | ✅ |
| Centralized Logging | ✅ کامل | ✅ | ✅ | ⏳ |

---

## 🚀 راه‌اندازی سریع

### 1. راه‌اندازی RabbitMQ و Redis

```bash
cd cloud
docker-compose up -d rabbitmq redis
```

### 2. راه‌اندازی ELK Stack

```bash
cd infrastructure/monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### 3. راه‌اندازی CI/CD

```bash
# CI به صورت خودکار اجرا می‌شود
# برای deployment:
gh workflow run deploy.yml -f environment=staging
```

---

## 📝 مثال‌های یکپارچه‌سازی

### مثال 1: استفاده از Message Queue در Data Collection

```python
# cloud/services/data-collection/app/main.py
from shared.message_queue import get_rabbitmq_client

mq = get_rabbitmq_client()

@app.post("/data/sensor")
async def receive_sensor_data(data: dict):
    # ارسال به queue برای پردازش ناهمزمان
    mq.publish_message(
        queue_name="sensor_data",
        message={
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        },
        persistent=True
    )
    return {"status": "queued"}
```

### مثال 2: استفاده از Redis Cache در API

```python
# cloud/services/api-gateway/app/main.py
from shared.redis_client import get_redis_client

redis = get_redis_client()

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    # بررسی cache
    cache_key = f"user:{user_id}"
    cached = redis.get_cache(cache_key)
    if cached:
        return cached
    
    # دریافت از DB
    user = db.query(User).filter(User.id == user_id).first()
    user_dict = {"id": user.id, "name": user.name}
    
    # ذخیره در cache
    redis.set_cache(cache_key, user_dict, ttl=3600)
    return user_dict
```

### مثال 3: استفاده از Centralized Logging

```python
# cloud/services/user-management/app/main.py
from shared.logging_config import setup_logging
from loguru import logger

# Setup logging
setup_logging(
    service_name="user-management",
    environment="production",
    log_level="INFO"
)

@app.post("/users")
async def create_user(user_data: dict):
    logger.info(f"Creating user: {user_data['email']}")
    # ...
    logger.success(f"User created: {user_id}")
```

### مثال 4: Worker با Message Queue

```python
# cloud/services/ml-service/app/worker.py
from shared.message_queue import get_rabbitmq_client
from shared.redis_client import get_redis_client

mq = get_rabbitmq_client()
redis = get_redis_client()

def process_ml_request(message: dict, delivery_tag: int) -> bool:
    request_id = message.get("request_id")
    
    # بررسی cache
    cache_key = f"ml_result:{request_id}"
    cached = redis.get_cache(cache_key)
    if cached:
        return cached
    
    # پردازش ML
    result = ml_inference(message['data'])
    
    # ذخیره در cache
    redis.set_cache(cache_key, result, ttl=3600)
    
    return True

# شروع worker
mq.consume_messages("ml_requests", process_ml_request)
```

---

## 🔧 تنظیمات

### متغیرهای محیطی

```bash
# RabbitMQ
export RABBITMQ_URL=amqp://admin:admin@localhost:5672/

# Redis
export REDIS_URL=redis://localhost:6379/0

# ELK
export LOGSTASH_HOST=logstash
export LOGSTASH_PORT=5044

# Sentry
export SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

### Docker Compose

```yaml
# cloud/docker-compose.yml
services:
  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "5672:5672"
      - "15672:15672"
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

---

## 📚 مستندات

- `cloud/services/MESSAGE_QUEUE_GUIDE.md` - راهنمای RabbitMQ
- `cloud/services/REDIS_CACHING_GUIDE.md` - راهنمای Redis
- `DEVOPS_CI_CD_GUIDE.md` - راهنمای CI/CD
- `infrastructure/monitoring/README.md` - راهنمای Monitoring

---

## 🎯 مزایا

### Message Queue:
- ✅ پردازش ناهمزمان
- ✅ Decoupling سرویس‌ها
- ✅ Buffering در زمان قطع ارتباط
- ✅ Scalability

### Redis:
- ✅ بهبود عملکرد با cache
- ✅ مدیریت session
- ✅ Rate limiting
- ✅ Real-time analytics

### CI/CD:
- ✅ Automated testing
- ✅ Automated deployment
- ✅ Blue-green deployment
- ✅ Rollback mechanism

### Centralized Logging:
- ✅ یکپارچه‌سازی لاگ‌ها
- ✅ جستجو و تحلیل
- ✅ Monitoring و Alerting
- ✅ Error tracking

---

## ⚠️ نکات مهم

### 1. Message Queue
- استفاده از persistent messages برای داده‌های مهم
- پیاده‌سازی retry mechanism
- مدیریت acknowledgment

### 2. Redis
- تنظیم TTL مناسب برای cache
- استفاده از pattern-based deletion برای cleanup
- Monitoring memory usage

### 3. CI/CD
- اجرای تست‌ها قبل از merge
- استفاده از blue-green برای production
- آماده‌سازی rollback mechanism

### 4. Logging
- استفاده از structured logging
- اضافه کردن context به لاگ‌ها
- تنظیم log levels مناسب

---

**تاریخ:** 2024  
**نسخه:** 1.0  
**وضعیت:** ✅ پیاده‌سازی کامل - آماده برای استفاده

