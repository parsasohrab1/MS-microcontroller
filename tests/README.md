# راهنمای تست‌ها

## ساختار تست‌ها

```
tests/
├── unit/                    # Unit tests
│   ├── test_data_collection.py
│   └── test_analytics.py
├── integration/             # Integration tests
│   ├── test_data_collection_integration.py
│   └── test_services_integration.py
├── e2e/                     # End-to-end tests
│   └── test_full_workflow.py
├── performance/             # Performance tests
│   └── locustfile.py
└── conftest.py             # Shared fixtures
```

---

## اجرای تست‌ها

### Unit Tests

```bash
# همه unit tests
pytest tests/unit/ -v

# تست خاص
pytest tests/unit/test_data_collection.py -v

# با coverage
pytest tests/unit/ --cov=cloud/services/data-collection --cov-report=html
```

### Integration Tests

```bash
# همه integration tests
pytest tests/integration/ -v

# نیاز به database و services
docker-compose up -d postgres redis rabbitmq
pytest tests/integration/ -v
```

### End-to-End Tests

```bash
# همه E2E tests
pytest tests/e2e/ -v

# نیاز به تمام services
docker-compose up -d
pytest tests/e2e/ -v
```

### Performance Tests

```bash
# با Locust
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

---

## Coverage

هدف: **≥90% code coverage**

```bash
# Generate coverage report
pytest --cov=cloud/services --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

---

## Best Practices

### 1. Unit Tests
- تست هر function به صورت جداگانه
- استفاده از mocks برای dependencies
- Fast execution

### 2. Integration Tests
- تست ارتباط بین components
- استفاده از test database
- Cleanup بعد از تست

### 3. E2E Tests
- تست complete workflows
- استفاده از actual services
- Realistic scenarios

---

**آخرین به‌روزرسانی:** 2024

