# راهنمای بهینه‌سازی API

## مقدمه

این راهنما نحوه استفاده از قابلیت‌های بهینه‌سازی API را توضیح می‌دهد.

---

## 1. GraphQL برای Query های پیچیده

### استفاده از GraphQL

```graphql
# Query مثال
query {
  patient(patientId: "patient_123") {
    id
    name
    email
    riskScore
    sensorData(startDate: "2024-01-01", limit: 100) {
      id
      timestamp
      eegData
      riskScore
    }
    predictions(limit: 10) {
      attackProbability
      attackSeverity
      confidence
    }
    alerts(level: "critical") {
      message
      timestamp
    }
  }
}
```

### Mutation مثال

```graphql
mutation {
  createPatient(input: {
    name: "John Doe"
    email: "john@example.com"
    patientId: "patient_123"
  }) {
    patient {
      id
      name
    }
  }
}
```

### استفاده در کد

```python
from fastapi import FastAPI
from starlette.graphql import GraphQLApp
from .graphql.schema import schema

app = FastAPI()
app.add_route("/graphql", GraphQLApp(schema=schema))
```

---

## 2. API Versioning

### استفاده از Versioning

```python
from cloud.services.api_gateway.app.versioning import (
    get_version_manager, version_middleware
)

# ثبت version
version_manager = get_version_manager()
version_manager.register_version("v1", v1_router)
version_manager.register_version("v2", v2_router)

# اضافه کردن middleware
app.middleware("http")(version_middleware)
```

### درخواست با Version

```bash
# از طریق Header
curl -H "Accept: application/vnd.api+json;version=v2" \
     http://api.example.com/api/users

# از طریق Query Parameter
curl http://api.example.com/api/users?version=v2

# از طریق Path
curl http://api.example.com/api/v2/users
```

### Deprecation

```python
# Deprecate کردن version
version_manager.deprecate_version("v1", sunset_date="2024-12-31")
```

---

## 3. Rate Limiting

### تنظیم Rate Limits

```python
from cloud.services.api_gateway.app.rate_limiting import (
    get_rate_limiter, RateLimitRule
)

rate_limiter = get_rate_limiter()

# تنظیم rule برای endpoint
rate_limiter.set_rule(
    "/api/v1/auth/login",
    RateLimitRule(
        requests_per_minute=5,
        requests_per_hour=20,
        requests_per_day=100
    )
)
```

### استفاده از Middleware

```python
from cloud.services.api_gateway.app.rate_limiting import rate_limit_middleware

app.middleware("http")(rate_limit_middleware)
```

### Response Headers

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

### Error Response

```json
{
  "error": "Rate limit exceeded",
  "message": "Rate limit exceeded: too many requests per minute",
  "retry_after": 60
}
```

---

## 4. Response Compression

### استفاده از Compression Middleware

```python
from cloud.services.api_gateway.app.response_compression import CompressionMiddleware

app.add_middleware(
    CompressionMiddleware,
    minimum_size=500,  # حداقل 500 bytes
    compress_level=6  # سطح فشرده‌سازی
)
```

### درخواست با Compression

```bash
# درخواست با GZIP
curl -H "Accept-Encoding: gzip" http://api.example.com/api/data

# درخواست با Brotli
curl -H "Accept-Encoding: br" http://api.example.com/api/data
```

### Response Headers

```
Content-Encoding: gzip
Content-Length: 1234
Vary: Accept-Encoding
X-Original-Content-Length: 5000
```

---

## بهترین روش‌ها

### 1. GraphQL
- استفاده برای queries پیچیده
- استفاده از fragments برای reuse
- استفاده از variables برای پارامترها
- محدود کردن depth و complexity

### 2. API Versioning
- استفاده از semantic versioning
- Deprecation با advance notice
- پشتیبانی از چند version همزمان
- Documentation برای هر version

### 3. Rate Limiting
- تنظیم limits مناسب برای هر endpoint
- استفاده از burst برای spikes
- Different limits برای authenticated/unauthenticated
- Monitoring و alerting

### 4. Response Compression
- فشرده‌سازی فقط برای text-based content
- استفاده از Brotli برای بهتر compression
- تنظیم minimum size
- Monitoring compression ratio

---

## نتایج مورد انتظار

با استفاده از این بهینه‌سازی‌ها:

- **GraphQL:** کاهش 50-70% در تعداد requests
- **Versioning:** پشتیبانی از چند version
- **Rate Limiting:** محافظت از API
- **Compression:** کاهش 60-80% در bandwidth

---

**آخرین به‌روزرسانی:** 2024

