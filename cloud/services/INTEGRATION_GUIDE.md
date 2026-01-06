# راهنمای یکپارچه‌سازی میکروسرویس‌ها

## مقدمه

این راهنما نحوه یکپارچه‌سازی و راه‌اندازی تمام میکروسرویس‌ها را توضیح می‌دهد.

---

## 1. ساختار سرویس‌ها

### سرویس‌های موجود:

1. **User Management Service** (Port 8001)
   - مدیریت کاربران
   - احراز هویت
   - RBAC

2. **Data Collection Service** (Port 8002)
   - جمع‌آوری داده از Gateway
   - اعتبارسنجی داده
   - ارسال به Message Queue

3. **ML Inference Service** (Port 8003)
   - پیش‌بینی با مدل‌های ML
   - Model Versioning
   - A/B Testing

4. **Analytics Service** (Port 8004)
   - تحلیل داده
   - گزارش‌گیری
   - Caching

5. **Notification Service** (Port 8005)
   - ارسال اعلان‌ها
   - Email, SMS, Push

6. **API Gateway** (Port 8000)
   - Routing
   - Rate Limiting
   - Versioning

---

## 2. راه‌اندازی

### 2.1 Prerequisites

```bash
# نصب Docker و Docker Compose
# نصب Python 3.10+
# نصب PostgreSQL
# نصب Redis
# نصب RabbitMQ
```

### 2.2 راه‌اندازی Infrastructure

```bash
# Start infrastructure services
docker-compose -f cloud/docker-compose.yml up -d

# این شامل:
# - PostgreSQL
# - Redis
# - RabbitMQ
```

### 2.3 راه‌اندازی سرویس‌ها

#### User Management Service:

```bash
cd cloud/services/user-management
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# تنظیم .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ms_neuroplatform
SECRET_KEY=your-secret-key

# اجرای migrations
alembic upgrade head

# اجرای سرویس
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

#### Data Collection Service:

```bash
cd cloud/services/data-collection
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# تنظیم .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ms_neuroplatform
RABBITMQ_URL=amqp://admin:admin@localhost:5672

# اجرای سرویس
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

#### ML Inference Service:

```bash
cd cloud/services/ml-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# اجرای سرویس
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

#### Analytics Service:

```bash
cd cloud/services/analytics-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# تنظیم .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ms_neuroplatform
REDIS_URL=redis://localhost:6379

# اجرای سرویس
uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

#### API Gateway:

```bash
cd cloud/services/api-gateway
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# اجرای سرویس
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 3. یکپارچه‌سازی

### 3.1 Flow داده

```
Gateway → Data Collection Service → Message Queue → ML Inference Service
                                                      ↓
                                              Analytics Service
                                                      ↓
                                              Notification Service
```

### 3.2 API Gateway Routing

```yaml
# Traefik configuration (docker-compose.yml)
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
    labels:
      - "traefik.http.routers.user-management.rule=Host(`api.example.com`) && PathPrefix(`/api/v1/users`)"
      - "traefik.http.services.user-management.loadbalancer.server.port=8001"
      - "traefik.http.routers.data-collection.rule=Host(`api.example.com`) && PathPrefix(`/api/v1/data`)"
      - "traefik.http.services.data-collection.loadbalancer.server.port=8002"
```

### 3.3 Message Queue Integration

```python
# در Data Collection Service
from app.message_queue import publish_to_queue

await publish_to_queue("sensor_data", {
    "data_id": data_id,
    "patient_id": patient_id,
    "timestamp": timestamp.isoformat()
})

# در ML Inference Service
from app.message_queue import consume_from_queue

async def process_sensor_data(message):
    # Process data
    prediction = await predict(message["data_id"])
    # Send to notification service
    await publish_to_queue("predictions", prediction)

await consume_from_queue("sensor_data", process_sensor_data)
```

---

## 4. تست

### 4.1 Unit Tests

```bash
# هر سرویس
cd cloud/services/<service-name>
pytest tests/unit/ -v
```

### 4.2 Integration Tests

```bash
# از root directory
pytest tests/integration/ -v
```

### 4.3 End-to-End Tests

```bash
# Start all services
docker-compose up -d

# Run E2E tests
pytest tests/e2e/ -v
```

### 4.4 Load Tests

```bash
# با Locust
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

---

## 5. Monitoring

### 5.1 Health Checks

```bash
# Check all services
curl http://localhost:8001/health  # User Management
curl http://localhost:8002/health  # Data Collection
curl http://localhost:8003/health  # ML Inference
curl http://localhost:8004/health  # Analytics
curl http://localhost:8000/health  # API Gateway
```

### 5.2 Logging

```bash
# Centralized logging با ELK
docker-compose -f infrastructure/monitoring/docker-compose.monitoring.yml up -d

# Access Kibana
# http://localhost:5601
```

### 5.3 Metrics

```bash
# Prometheus metrics
# http://localhost:9090

# Grafana dashboards
# http://localhost:3000
```

---

## 6. Deployment

### 6.1 Docker

```bash
# Build images
docker build -t user-management:latest -f cloud/services/user-management/Dockerfile .
docker build -t data-collection:latest -f cloud/services/data-collection/Dockerfile .
# ...

# Run with docker-compose
docker-compose up -d
```

### 6.2 Kubernetes

```bash
# Apply configurations
kubectl apply -f cloud/infrastructure/kubernetes/

# Check status
kubectl get pods
kubectl get services
```

---

## 7. Troubleshooting

### مشکل: سرویس شروع نمی‌شود

```bash
# بررسی logs
docker-compose logs <service-name>

# بررسی database connection
psql -h localhost -U postgres -d ms_neuroplatform
```

### مشکل: Message Queue connection failed

```bash
# بررسی RabbitMQ
docker-compose logs rabbitmq

# بررسی connection
rabbitmqctl list_queues
```

### مشکل: Redis connection failed

```bash
# بررسی Redis
docker-compose logs redis

# تست connection
redis-cli ping
```

---

## 8. Best Practices

### 8.1 Error Handling
- استفاده از try-except در همه endpoints
- Logging مناسب
- Return meaningful error messages

### 8.2 Caching
- Cache نتایج پراستفاده
- TTL مناسب
- Cache invalidation

### 8.3 Rate Limiting
- اعمال rate limiting در API Gateway
- Per-user limits
- Per-endpoint limits

### 8.4 Security
- استفاده از HTTPS
- Authentication در همه endpoints
- RBAC برای authorization

---

**آخرین به‌روزرسانی:** 2024

