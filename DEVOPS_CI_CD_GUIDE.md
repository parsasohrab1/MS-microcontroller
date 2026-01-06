# راهنمای DevOps و CI/CD

## مقدمه

این راهنما نحوه استفاده از قابلیت‌های DevOps و CI/CD را توضیح می‌دهد.

---

## 1. CI/CD Pipeline

### GitHub Actions Workflows

#### CI Pipeline (`.github/workflows/ci.yml`):
- ✅ Unit tests
- ✅ Integration tests
- ✅ End-to-end tests
- ✅ Performance tests
- ✅ Security tests
- ✅ Linting
- ✅ Docker image builds

#### Deployment Pipeline (`.github/workflows/deploy.yml`):
- ✅ Staging deployment
- ✅ Production deployment (Blue-Green)
- ✅ Rollback mechanism
- ✅ Health checks
- ✅ Smoke tests

### استفاده:

```bash
# CI Pipeline به صورت خودکار اجرا می‌شود در:
# - Push به main/develop
# - Pull requests

# Deployment Pipeline:
# - Push به main → Deploy to staging
# - Manual trigger → Deploy to production
```

---

## 2. Infrastructure as Code

### Terraform

```bash
# Initialize
cd infrastructure/terraform
terraform init

# Plan
terraform plan -var="environment=staging"

# Apply
terraform apply -var="environment=staging"
```

### Ansible

```bash
# Deploy to staging
ansible-playbook -i inventory/staging deploy-staging.yml

# Deploy to production
ansible-playbook -i inventory/production deploy-production.yml
```

---

## 3. Monitoring و Logging

### Centralized Logging (ELK Stack)

```bash
# Start ELK Stack
docker-compose -f infrastructure/monitoring/docker-compose.monitoring.yml up -d

# Access Kibana
# http://localhost:5601
```

### Application Performance Monitoring (Prometheus + Grafana)

```bash
# Start Prometheus and Grafana
docker-compose -f infrastructure/monitoring/docker-compose.monitoring.yml up -d prometheus grafana

# Access Prometheus
# http://localhost:9090

# Access Grafana
# http://localhost:3000
# Username: admin
# Password: admin
```

### Error Tracking (Sentry)

```bash
# Start Sentry
docker-compose -f infrastructure/monitoring/docker-compose.monitoring.yml up -d sentry

# Access Sentry
# http://localhost:9000
```

### استفاده در کد:

```python
# Logging
from cloud.services.shared.logging_config import setup_logging

setup_logging(
    service_name="user-management",
    environment="production",
    elk_enabled=True
)

# Monitoring
from cloud.services.shared.monitoring import start_monitoring, monitor_http_request

start_monitoring(port=9090)

@monitor_http_request(endpoint="/api/v1/users")
async def get_users():
    # ...
    pass

# Error Tracking
from cloud.services.shared.error_tracking import init_sentry, capture_exception

init_sentry(dsn=os.getenv("SENTRY_DSN"))

try:
    # ...
except Exception as e:
    capture_exception(e)
```

---

## 4. Containerization

### Docker

```bash
# Build image
docker build -t user-management:latest -f cloud/services/user-management/Dockerfile .

# Run container
docker run -p 8001:8001 user-management:latest
```

### Docker Compose

```bash
# Start all services
docker-compose -f cloud/docker-compose.yml up -d

# Stop all services
docker-compose -f cloud/docker-compose.yml down
```

---

## 5. Testing

### Unit Tests

```bash
# Run unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ -v --cov=. --cov-report=html
```

### Integration Tests

```bash
# Run integration tests
pytest tests/integration/ -v
```

### End-to-End Tests

```bash
# Start services
docker-compose up -d

# Run E2E tests
pytest tests/e2e/ -v
```

### Performance Tests

```bash
# Run Locust
locust -f tests/performance/locustfile.py --headless -u 100 -r 10 -t 60s
```

### Security Tests

```bash
# Run Bandit
bandit -r cloud/

# Run Safety
safety check

# Run Trivy
trivy fs .
```

---

## بهترین روش‌ها

### 1. CI/CD
- اجرای تست‌ها قبل از merge
- Automated deployment
- Blue-green deployment برای production
- Rollback mechanism

### 2. Infrastructure as Code
- استفاده از Terraform برای infrastructure
- استفاده از Ansible برای configuration
- Version control برای همه configurations

### 3. Monitoring
- Centralized logging
- APM برای performance
- Error tracking
- Alerting

### 4. Containerization
- Multi-stage builds
- Non-root users
- Health checks
- Resource limits

---

**آخرین به‌روزرسانی:** 2024

