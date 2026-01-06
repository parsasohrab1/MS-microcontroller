# راهنمای بهینه‌سازی پایگاه داده

## مقدمه

این راهنما نحوه استفاده از قابلیت‌های بهینه‌سازی پایگاه داده را توضیح می‌دهد.

---

## 1. Indexing بهینه

### ایجاد Index

```python
from cloud.services.shared.database_optimization import DatabaseOptimizer
from cloud.services.user_management.app.database import get_db

db = next(get_db())
optimizer = DatabaseOptimizer(db)

# ایجاد index ساده
optimizer.create_indexes("users", ["email"], unique=True)

# ایجاد composite index
optimizer.create_indexes("sensor_data", ["patient_id", "timestamp"])

# ایجاد GIN index برای JSONB
optimizer.create_composite_index(
    "sensor_data",
    ["data"],
    index_type="gin"
)
```

### بررسی آمار Index

```python
# دریافت آمار استفاده از index
stats = optimizer.get_index_usage_stats("sensor_data")

for stat in stats:
    print(f"Index: {stat['index_name']}")
    print(f"Scans: {stat['scans']}")
    print(f"Tuples read: {stat['tuples_read']}")
```

### اجرای ANALYZE

```python
# به‌روزرسانی آمار برای query planner
optimizer.analyze_table("sensor_data")
```

---

## 2. Partitioning داده‌های قدیمی

### ایجاد Partitioned Table

```python
# ایجاد partitioned table
optimizer.create_partitioned_table(
    "sensor_data",
    "timestamp",
    partition_type="range"
)
```

### ایجاد Partition برای ماه جدید

```python
# ایجاد partition برای ماه جاری
from datetime import datetime

now = datetime.now()
optimizer.create_partition_for_month(
    "sensor_data",
    now.year,
    now.month
)
```

### آرشیو Partitions قدیمی

```python
# آرشیو partitions قدیمی‌تر از 1 سال
archived = optimizer.archive_old_partitions(
    "sensor_data",
    older_than_days=365
)

print(f"Archived {len(archived)} partitions")
```

---

## 3. استفاده از Read Replicas

### مقداردهی اولیه

```python
from cloud.services.shared.read_replica import init_replica_manager

# مقداردهی اولیه
replica_manager = init_replica_manager(
    primary_db_url="postgresql://user:pass@primary:5432/db",
    replica_urls=[
        "postgresql://user:pass@replica1:5432/db",
        "postgresql://user:pass@replica2:5432/db"
    ]
)
```

### استفاده برای Read Operations

```python
from cloud.services.shared.read_replica import get_replica_manager

replica_manager = get_replica_manager()

# استفاده از read session
with replica_manager.read_session() as session:
    users = session.query(User).all()
```

### استفاده برای Write Operations

```python
# استفاده از write session (همیشه primary)
with replica_manager.write_session() as session:
    new_user = User(email="test@example.com")
    session.add(new_user)
```

### Load Balancing

```python
# استفاده از load balanced session
session = replica_manager.get_load_balanced_session()
users = session.query(User).all()
```

### بررسی سلامت Replicas

```python
# بررسی سلامت همه replicas
replica_manager.check_all_replicas_health()

# دریافت آمار
stats = replica_manager.get_replica_stats()
for stat in stats:
    print(f"Replica {stat['replica_index']}:")
    print(f"  Healthy: {stat['healthy']}")
    print(f"  Lag: {stat['lag_ms']} ms")
```

---

## 4. Query Optimization

### تحلیل Query

```python
from cloud.services.shared.query_optimizer import QueryOptimizer

optimizer = QueryOptimizer(db)

# تحلیل query
result = optimizer.analyze_query_performance(
    "SELECT * FROM sensor_data WHERE patient_id = :patient_id",
    params={"patient_id": "patient_123"}
)

print(f"Execution time: {result['execution_time_ms']} ms")
print(f"Suggestions: {result['optimization_suggestions']}")
```

### بهینه‌سازی SELECT Query

```python
from sqlalchemy.orm import Query

# بهینه‌سازی query
query = session.query(SensorData)
optimized_query = optimizer.optimize_select_query(
    query,
    limit=100,
    offset=0
)

results = optimized_query.all()
```

### Pagination

```python
# اضافه کردن pagination
query = session.query(SensorData)
paginated_query = optimizer.add_pagination(query, page=1, page_size=50)
results = paginated_query.all()
```

### Bulk Insert

```python
# بهینه‌سازی bulk insert
data = [
    {"patient_id": "patient_1", "value": 1.5},
    {"patient_id": "patient_2", "value": 2.3},
    # ... more data
]

optimizer.optimize_bulk_insert("sensor_data", data)
```

### Materialized Views

```python
# ایجاد materialized view
optimizer.create_materialized_view(
    "patient_stats_view",
    """
    SELECT 
        patient_id,
        COUNT(*) as total_readings,
        AVG(value) as avg_value,
        MAX(timestamp) as last_reading
    FROM sensor_data
    GROUP BY patient_id
    """
)

# Refresh view
optimizer.refresh_materialized_view("patient_stats_view", concurrently=True)
```

---

## 5. Maintenance

### VACUUM

```python
# اجرای VACUUM
optimizer.vacuum_table("sensor_data", analyze=True)
```

### REINDEX

```python
# Rebuild indexes
optimizer.reindex_table("sensor_data")
```

---

## بهترین روش‌ها

### 1. Indexing
- ایجاد index روی ستون‌های مورد استفاده در WHERE, JOIN, ORDER BY
- استفاده از composite indexes برای queries چندستونی
- استفاده از GIN indexes برای JSONB columns
- بررسی آمار استفاده از index و حذف indexes غیرضروری

### 2. Partitioning
- استفاده از partitioning برای جداول بزرگ (>10M rows)
- Partition بر اساس timestamp برای داده‌های سری زمانی
- آرشیو partitions قدیمی به صورت دوره‌ای

### 3. Read Replicas
- استفاده از replicas برای read operations
- همیشه از primary برای write operations
- بررسی سلامت replicas به صورت دوره‌ای
- استفاده از load balancing برای توزیع بار

### 4. Query Optimization
- استفاده از EXPLAIN ANALYZE برای تحلیل queries
- اضافه کردن LIMIT برای queries بزرگ
- استفاده از pagination
- استفاده از bulk operations برای inserts/updates

---

## نتایج مورد انتظار

با استفاده از این بهینه‌سازی‌ها:

- **Query Performance:** بهبود 50-90%
- **Read Throughput:** افزایش 3-5x با replicas
- **Storage:** کاهش 30-50% با partitioning
- **Maintenance Time:** کاهش 70% با automated tasks

---

**آخرین به‌روزرسانی:** 2024

