# راهنمای سریع زیرساخت Backend

## 🚀 راه‌اندازی سریع

### 1. راه‌اندازی Message Queue و Redis

```bash
cd cloud
docker-compose up -d rabbitmq redis
```

**دسترسی:**
- RabbitMQ Management UI: http://localhost:15672 (admin/admin)
- Redis: localhost:6379

### 2. راه‌اندازی Centralized Logging (ELK Stack)

```bash
cd infrastructure/monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

**دسترسی:**
- Kibana: http://localhost:5601
- Elasticsearch: http://localhost:9200
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### 3. CI/CD Pipeline

CI Pipeline به صورت خودکار در Push/PR اجرا می‌شود.

**Manual Deployment:**
```bash
gh workflow run deploy.yml -f environment=staging
```

---

## 📝 مثال‌های استفاده

### Message Queue

```python
from shared.message_queue import get_rabbitmq_client

mq = get_rabbitmq_client()

# ارسال پیام
mq.publish_message("sensor_data", {"value": 42.5})

# دریافت پیام
def process(message, delivery_tag):
    print(message)
    return True

mq.consume_messages("sensor_data", process)
```

### Redis Cache

```python
from shared.redis_client import get_redis_client

redis = get_redis_client()

# Cache
redis.set_cache("user:123", {"name": "John"}, ttl=3600)
user = redis.get_cache("user:123")

# Session
redis.set_session("session_id", user_id=123, ttl=3600)

# Rate Limiting
allowed, remaining, reset = redis.check_rate_limit(
    identifier="192.168.1.1",
    max_requests=100,
    window_seconds=3600
)
```

### Centralized Logging

```python
from shared.logging_config import setup_logging
from loguru import logger

setup_logging(
    service_name="user-management",
    environment="production",
    log_level="INFO"
)

logger.info("User created", user_id=123, email="user@example.com")
```

---

## 🔧 تنظیمات

### متغیرهای محیطی

```bash
# RabbitMQ
export RABBITMQ_URL=amqp://admin:admin@localhost:5672/

# Redis
export REDIS_URL=redis://localhost:6379/0

# Logging
export LOGSTASH_HOST=logstash
export LOGSTASH_PORT=5044
```

---

## 📚 مستندات کامل

- `BACKEND_INFRASTRUCTURE_SUMMARY.md` - خلاصه کامل
- `cloud/services/MESSAGE_QUEUE_GUIDE.md` - راهنمای RabbitMQ
- `cloud/services/REDIS_CACHING_GUIDE.md` - راهنمای Redis
- `DEVOPS_CI_CD_GUIDE.md` - راهنمای CI/CD

---

**آماده برای استفاده! 🎉**

