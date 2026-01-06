# راهنمای مقیاس‌پذیری Backend

## مقدمه

این راهنما نحوه استفاده از قابلیت‌های مقیاس‌پذیری Backend را توضیح می‌دهد.

---

## 1. Load Balancing

### Nginx Load Balancer

```bash
# راه‌اندازی Nginx Load Balancer
docker-compose -f docker-compose.scaling.yml up -d nginx
```

### تنظیمات Load Balancing

```nginx
# در nginx.conf
upstream backend_servers {
    least_conn;  # یا round_robin, ip_hash
    
    server backend1:8000 weight=3;
    server backend2:8000 weight=3;
    server backend3:8000 weight=2;
}
```

### Health Checks

```nginx
# Health check برای backend servers
server backend1:8000 max_fails=3 fail_timeout=30s;
```

### Rate Limiting

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;

location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    proxy_pass http://backend_servers;
}
```

---

## 2. Auto-Scaling

### Docker Compose Scaling

```bash
# Scale کردن service
docker-compose -f docker-compose.scaling.yml up -d --scale backend=5
```

### Kubernetes HPA

```yaml
# استفاده از HorizontalPodAutoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: user-management-hpa
spec:
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        averageUtilization: 70
```

### Python Auto-Scaling Manager

```python
from cloud.infrastructure.auto_scaling.scaling_manager import (
    AutoScalingManager, ScalingPolicy
)

# ایجاد scaling manager
manager = AutoScalingManager()

# ثبت سرویس
policy = ScalingPolicy(
    service_name="user-management",
    min_instances=2,
    max_instances=10,
    target_cpu=70.0,
    target_memory=80.0,
    scale_up_cooldown=60,
    scale_down_cooldown=300
)

manager.register_service(policy)

# شروع monitoring
await manager.start_monitoring(interval=30)
```

---

## 3. CDN برای Static Content

### مقداردهی اولیه CDN

```python
from cloud.infrastructure.cdn.cdn_manager import CDNManager, CDNConfig

# تنظیمات CDN
config = CDNConfig(
    provider="cloudflare",
    endpoint="https://cdn.example.com",
    api_key="your_api_key",
    zone_id="your_zone_id",
    cache_ttl=3600,
    enable_compression=True,
    enable_minification=True
)

cdn = CDNManager(config)
```

### آپلود فایل‌های Static

```python
# آپلود فایل
url = await cdn.upload_static_file(
    "static/js/app.js",
    cdn_path="js/app.js",
    content_type="application/javascript"
)

print(f"CDN URL: {url}")
```

### آپلود دایرکتوری

```python
# آپلود کل دایرکتوری
urls = await cdn.upload_directory(
    "static/",
    base_cdn_path="assets/",
    extensions=[".js", ".css", ".png", ".jpg"]
)
```

### پاک کردن Cache

```python
# Invalidate cache
success = await cdn.invalidate_cache([
    "js/app.js",
    "css/styles.css"
])
```

---

## 4. Database Sharding

### مقداردهی اولیه Sharding

```python
from cloud.services.shared.database_sharding import (
    init_shard_manager, ShardingStrategy
)

# تنظیمات shards
shard_configs = [
    {"url": "postgresql://user:pass@db1:5432/db"},
    {"url": "postgresql://user:pass@db2:5432/db"},
    {"url": "postgresql://user:pass@db3:5432/db"}
]

# مقداردهی اولیه
shard_manager = init_shard_manager(
    shard_configs,
    sharding_key="patient_id",
    strategy=ShardingStrategy.HASH
)
```

### استفاده از Sharded Database

```python
from cloud.services.shared.database_sharding import get_shard_manager

shard_manager = get_shard_manager()

# استفاده از shard session
patient_id = "patient_123"

with shard_manager.shard_session(patient_id) as session:
    # Query در shard مناسب
    results = session.query(SensorData).filter_by(
        patient_id=patient_id
    ).all()
```

### Query روی همه Shards

```python
# Query روی همه shards
def query_all_patients(session):
    return session.query(Patient).all()

all_patients = shard_manager.query_all_shards(query_all_patients)
```

### دریافت آمار Shards

```python
# آمار shards
stats = shard_manager.get_shard_stats()

for stat in stats:
    print(f"Shard {stat['shard_index']}:")
    print(f"  Records: {stat['record_count']}")
    print(f"  Size: {stat['database_size_mb']} MB")
```

---

## بهترین روش‌ها

### 1. Load Balancing
- استفاده از least_conn برای توزیع یکنواخت
- تنظیم health checks
- استفاده از rate limiting
- SSL/TLS termination در load balancer

### 2. Auto-Scaling
- تنظیم min/max replicas مناسب
- استفاده از CPU و Memory metrics
- تنظیم cooldown periods
- Monitoring و alerting

### 3. CDN
- آپلود static assets به CDN
- استفاده از compression و minification
- تنظیم cache TTL مناسب
- Invalidate cache در صورت نیاز

### 4. Database Sharding
- انتخاب sharding key مناسب
- استفاده از hash-based sharding برای توزیع یکنواخت
- Monitoring توزیع داده
- Rebalancing دوره‌ای

---

## نتایج مورد انتظار

با استفاده از این بهینه‌سازی‌ها:

- **Load Balancing:** توزیع یکنواخت بار
- **Auto-Scaling:** پاسخ خودکار به تغییرات بار
- **CDN:** کاهش 80-90% در bandwidth
- **Sharding:** مقیاس‌پذیری افقی پایگاه داده

---

**آخرین به‌روزرسانی:** 2024

