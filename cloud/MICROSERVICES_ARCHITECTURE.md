# معماری Microservices - سیستم نوروپلتفرم MS

## 📋 فهرست مطالب

1. [معماری کلی](#معماری-کلی)
2. [سرویس‌ها](#سرویس‌ها)
3. [API Gateway](#api-gateway)
4. [Service Discovery](#service-discovery)
5. [ارتباطات بین سرویس‌ها](#ارتباطات-بین-سرویس‌ها)
6. [پیاده‌سازی](#پیاده‌سازی)
7. [استقرار](#استقرار)

---

## معماری کلی

```
┌─────────────────────────────────────────────────────────────┐
│                        API Gateway                            │
│                    (Kong / Traefik)                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
│   User       │ │   Data     │ │    ML      │
│ Management   │ │ Collection │ │ Inference  │
│   Service    │ │  Service   │ │  Service   │
└───────┬──────┘ └─────┬──────┘ └─────┬──────┘
        │              │               │
┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
│ Notification │ │ Analytics  │ │  Gateway   │
│   Service    │ │  Service   │ │  Service   │
└──────────────┘ └────────────┘ └────────────┘
        │              │               │
        └──────────────┼───────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
│  PostgreSQL  │ │   Redis    │ │ RabbitMQ   │
│   (Primary)  │ │  (Cache)   │ │  (Queue)   │
└──────────────┘ └────────────┘ └────────────┘
```

---

## سرویس‌ها

### 1. User Management Service
**مسئولیت:**
- مدیریت کاربران (بیماران، پزشکان، ادمین‌ها)
- احراز هویت و مجوزدهی
- مدیریت جلسات (sessions)
- مدیریت پروفایل‌ها

**پورت:** 8001  
**پایگاه داده:** PostgreSQL (schema: users)  
**API Endpoints:**
- `POST /auth/register` - ثبت نام
- `POST /auth/login` - ورود
- `POST /auth/refresh` - تازه‌سازی توکن
- `GET /users/{user_id}` - دریافت اطلاعات کاربر
- `PUT /users/{user_id}` - به‌روزرسانی کاربر
- `DELETE /users/{user_id}` - حذف کاربر

### 2. Data Collection Service
**مسئولیت:**
- دریافت و ذخیره داده‌های سنسورها
- دریافت داده‌های EEG/ECoG
- دریافت داده‌های بیومارکرها
- مدیریت بافر داده‌ها

**پورت:** 8002  
**پایگاه داده:** PostgreSQL (schema: sensor_data)  
**Message Queue:** RabbitMQ (topic: sensor.data)  
**API Endpoints:**
- `POST /data/sensor` - ارسال داده سنسور
- `POST /data/eeg` - ارسال داده EEG
- `POST /data/biomarker` - ارسال داده بیومارکر
- `GET /data/patient/{patient_id}` - دریافت داده‌های بیمار
- `GET /data/patient/{patient_id}/latest` - آخرین داده‌ها

### 3. ML Inference Service
**مسئولیت:**
- اجرای مدل‌های ML برای پیش‌بینی
- پردازش ویژگی‌ها
- تولید پیش‌بینی‌ها
- مدیریت نسخه‌های مدل

**پورت:** 8003  
**Message Queue:** RabbitMQ (topic: ml.inference)  
**API Endpoints:**
- `POST /ml/predict` - پیش‌بینی
- `POST /ml/batch-predict` - پیش‌بینی دسته‌ای
- `GET /ml/models` - لیست مدل‌ها
- `POST /ml/models/{model_id}/load` - بارگذاری مدل
- `GET /ml/health` - سلامت سرویس

### 4. Notification Service
**مسئولیت:**
- ارسال اعلان‌ها به کاربران
- مدیریت کانال‌های اعلان (Email, SMS, Push)
- زمان‌بندی اعلان‌ها
- مدیریت ترجیحات کاربران

**پورت:** 8004  
**Message Queue:** RabbitMQ (topic: notifications)  
**API Endpoints:**
- `POST /notifications/send` - ارسال اعلان
- `POST /notifications/schedule` - زمان‌بندی اعلان
- `GET /notifications/user/{user_id}` - دریافت اعلان‌های کاربر
- `PUT /notifications/preferences` - تنظیم ترجیحات

### 5. Analytics Service
**مسئولیت:**
- تحلیل داده‌های جمع‌آوری شده
- تولید گزارش‌ها
- آمار و متریک‌ها
- پیش‌بینی‌های درازمدت

**پورت:** 8005  
**پایگاه داده:** PostgreSQL (schema: analytics)  
**Cache:** Redis  
**API Endpoints:**
- `GET /analytics/patient/{patient_id}/summary` - خلاصه بیمار
- `GET /analytics/patient/{patient_id}/trends` - روندها
- `GET /analytics/reports/generate` - تولید گزارش
- `GET /analytics/metrics` - متریک‌ها

### 6. Gateway Service (موجود)
**مسئولیت:**
- ارتباط با دستگاه‌های پوشیدنی
- دریافت داده از Gateway
- همگام‌سازی با سرویس‌های دیگر

**پورت:** 8006  
**Message Queue:** RabbitMQ (topic: gateway.data)

---

## API Gateway

### استفاده از Kong یا Traefik

**Kong:**
- پلاگین‌های قدرتمند
- مدیریت API
- Rate limiting
- Authentication

**Traefik:**
- ساده‌تر
- Auto-discovery
- Let's Encrypt integration

**پیکربندی:**
- Routing به سرویس‌ها
- Load balancing
- SSL/TLS termination
- Rate limiting
- Authentication middleware

---

## Service Discovery

### استفاده از Consul یا Eureka

**Consul:**
- Service discovery
- Health checking
- Key-value store
- Multi-datacenter

**Eureka (Netflix):**
- ساده‌تر
- مناسب برای Spring Boot

**پیاده‌سازی:**
- هر سرویس خود را ثبت می‌کند
- Health check endpoint
- Auto-deregistration در صورت shutdown

---

## ارتباطات بین سرویس‌ها

### 1. Synchronous (HTTP/REST)
- برای درخواست‌های فوری
- مثال: دریافت اطلاعات کاربر
- استفاده از `httpx` یا `requests`

### 2. Asynchronous (Message Queue)
- برای پردازش ناهمزمان
- مثال: ارسال اعلان‌ها
- استفاده از RabbitMQ

### 3. Event-Driven
- برای رویدادهای سیستم
- مثال: رویداد "داده جدید دریافت شد"
- استفاده از RabbitMQ Topics

---

## پیاده‌سازی

### ساختار پوشه‌ها

```
cloud/
├── services/
│   ├── user-management/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models.py
│   │   │   ├── routers/
│   │   │   ├── services/
│   │   │   └── database.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── data-collection/
│   ├── ml-inference/
│   ├── notification/
│   └── analytics/
├── api-gateway/
│   ├── kong.yml
│   └── traefik.yml
├── docker-compose.yml
└── README.md
```

---

## استقرار

### Docker Compose (Development)

```yaml
version: '3.8'

services:
  # Databases
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ms_neuroplatform
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
  
  # Services
  user-management:
    build: ./services/user-management
    ports:
      - "8001:8001"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/ms_neuroplatform
      REDIS_URL: redis://redis:6379
  
  data-collection:
    build: ./services/data-collection
    ports:
      - "8002:8002"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/ms_neuroplatform
      RABBITMQ_URL: amqp://rabbitmq:5672
  
  # ... سایر سرویس‌ها
  
  # API Gateway
  api-gateway:
    image: traefik:v2.10
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./api-gateway/traefik.yml:/traefik.yml
```

### Kubernetes (Production)

```yaml
# Deployment example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-management
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-management
  template:
    metadata:
      labels:
        app: user-management
    spec:
      containers:
      - name: user-management
        image: ms-neuroplatform/user-management:latest
        ports:
        - containerPort: 8001
```

---

## مزایا

1. **مقیاس‌پذیری:** هر سرویس به صورت مستقل مقیاس می‌شود
2. **قابلیت اطمینان:** خرابی یک سرویس کل سیستم را متوقف نمی‌کند
3. **توسعه مستقل:** تیم‌ها می‌توانند به صورت مستقل کار کنند
4. **تکنولوژی‌های مختلف:** هر سرویس می‌تواند از تکنولوژی مناسب استفاده کند
5. **استقرار مستقل:** به‌روزرسانی یک سرویس بدون تأثیر بر سایرین

---

## چالش‌ها و راهکارها

### 1. Distributed Transactions
**مشکل:** تراکنش‌های توزیع‌شده پیچیده هستند  
**راهکار:** استفاده از Saga Pattern یا Event Sourcing

### 2. Service Communication
**مشکل:** Latency و خطا در ارتباطات  
**راهکار:** Circuit Breaker، Retry، Timeout

### 3. Data Consistency
**مشکل:** هماهنگی داده‌ها بین سرویس‌ها  
**راهکار:** Eventual Consistency، CQRS

### 4. Monitoring
**مشکل:** ردیابی درخواست‌ها در چند سرویس  
**راهکار:** Distributed Tracing (Jaeger, Zipkin)

---

## منابع

- [Microservices Patterns](https://microservices.io/patterns/)
- [Kong Documentation](https://docs.konghq.com/)
- [RabbitMQ Tutorials](https://www.rabbitmq.com/getstarted.html)
- [Docker Compose](https://docs.docker.com/compose/)

---

**آخرین به‌روزرسانی:** 2024

