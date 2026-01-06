# راهنمای امنیت Backend و احراز هویت

## مقدمه

این راهنما نحوه استفاده از قابلیت‌های امنیت Backend و احراز هویت را توضیح می‌دهد.

---

## 1. OAuth 2.0 / OpenID Connect

### استفاده از OAuth 2.0

```python
from cloud.services.user_management.app.security import (
    get_oauth2_provider,
    get_current_user,
    TokenData
)

# دریافت OAuth2 provider
oauth2 = get_oauth2_provider()

# دریافت authorization URL
state = "random_state_string"
scopes = ["openid", "profile", "email"]
auth_url = oauth2.get_authorization_url(state, scopes)

# بعد از redirect، exchange code برای token
code = request.query_params.get("code")
token_response = await oauth2.exchange_code_for_token(code)

# دریافت user info
user_info = await oauth2.get_user_info(token_response["access_token"])
```

### استفاده در FastAPI

```python
from fastapi import Depends
from cloud.services.user_management.app.security import get_current_user, TokenData

@app.get("/api/v1/profile")
async def get_profile(current_user: TokenData = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "email": current_user.email
    }
```

---

## 2. Role-Based Access Control (RBAC)

### استفاده از RBAC

```python
from cloud.services.user_management.app.security import (
    Role,
    Permission,
    require_role,
    require_permission,
    RBACManager
)

# بررسی نقش
@app.get("/api/v1/admin/users")
async def get_users(
    current_user: TokenData = Depends(require_role(Role.ADMIN))
):
    # فقط admin دسترسی دارد
    return {"users": []}

# بررسی مجوز
@app.get("/api/v1/patients/{patient_id}")
async def get_patient(
    patient_id: str,
    current_user: TokenData = Depends(
        require_permission(Permission.VIEW_PATIENT_DATA)
    )
):
    # بررسی دسترسی
    if not check_patient_access(current_user.user_id, patient_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {"patient_id": patient_id}
```

### نقش‌ها و مجوزها

```python
# نقش‌های موجود
Role.ADMIN      # دسترسی کامل
Role.DOCTOR     # دسترسی به داده‌های patient و treatment
Role.NURSE      # دسترسی محدود به داده‌ها
Role.PATIENT    # فقط داده‌های خودش
Role.RESEARCHER # فقط داده‌های anonymized

# بررسی مجوز
has_permission = RBACManager.has_permission(
    Role.DOCTOR,
    Permission.VIEW_PATIENT_DATA
)
```

---

## 3. Audit Logging

### استفاده از Audit Logging

```python
from cloud.services.user_management.app.security import (
    get_audit_logger,
    AuditEventType
)

# دریافت audit logger
audit_logger = get_audit_logger(db)

# ثبت دسترسی به داده
audit_logger.log_data_access(
    user_id="user_123",
    user_email="user@example.com",
    resource_type="patient",
    resource_id="patient_456",
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)

# ثبت تغییرات
audit_logger.log_data_modification(
    user_id="user_123",
    user_email="user@example.com",
    resource_type="patient",
    resource_id="patient_456",
    action="update",
    old_data={"name": "Old Name"},
    new_data={"name": "New Name"}
)

# ثبت احراز هویت
audit_logger.log_authentication(
    user_id="user_123",
    user_email="user@example.com",
    event_type=AuditEventType.LOGIN,
    ip_address=request.client.host,
    success=True
)
```

### دریافت Audit Logs

```python
# دریافت logs
logs = audit_logger.get_audit_logs(
    user_id="user_123",
    event_type=AuditEventType.VIEW_PATIENT_DATA,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    limit=100
)
```

---

## 4. Data Anonymization

### استفاده از Data Anonymization

```python
from cloud.services.user_management.app.security import get_data_anonymizer

# دریافت anonymizer
anonymizer = get_data_anonymizer()

# Anonymize کردن داده‌های patient
patient_data = {
    "patient_id": "patient_123",
    "name": "John Doe",
    "email": "john@example.com",
    "birth_date": "1980-01-15",
    "age": 44,
    "location": "Tehran, Iran"
}

anonymized = anonymizer.anonymize_patient_data(
    patient_data,
    anonymization_level="high"  # low, medium, high
)

# Anonymize کردن داده‌های sensor
sensor_data = [
    {"timestamp": "2024-01-01T10:00:00", "value": 1.23},
    {"timestamp": "2024-01-01T10:01:00", "value": 1.45}
]

anonymized_sensor = anonymizer.anonymize_sensor_data(
    sensor_data,
    anonymization_level="medium"
)

# Anonymize کردن داده‌های treatment
treatment_data = {
    "patient_id": "patient_123",
    "doctor_id": "doctor_456",
    "start_date": "2024-01-01",
    "dosage": 50
}

anonymized_treatment = anonymizer.anonymize_treatment_data(
    treatment_data,
    anonymization_level="high"
)
```

### روش‌های Anonymization

```python
from cloud.services.user_management.app.security import AnonymizationMethod

# Hash کردن
hashed = AnonymizationMethod.hash_value("sensitive_data", salt="salt")

# Pseudonymization
mapping = {}
pseudonym = AnonymizationMethod.pseudonymize("John Doe", mapping)

# Generalization تاریخ
date = datetime(2024, 1, 15)
generalized = AnonymizationMethod.generalize_date(date, "year")  # "2024"

# Generalization سن
age_range = AnonymizationMethod.generalize_age(44, range_size=10)  # "40-50"

# اضافه کردن noise
noisy_value = AnonymizationMethod.add_noise(1.23, noise_level=0.1)
```

---

## 5. Penetration Testing

### اجرای Penetration Test

```python
from cloud.services.user_management.app.security import run_penetration_test

# اجرای تست
base_url = "https://api.example.com"
report = await run_penetration_test(base_url)

# بررسی نتایج
print(f"Total tests: {report['total_tests']}")
print(f"Passed: {report['passed']}")
print(f"Failed: {report['failed']}")
print(f"Critical issues: {report['severity_counts']['critical']}")

# بررسی تست‌های خاص
for result in report['results']:
    if not result['passed']:
        print(f"Failed: {result['test_name']} - {result['description']}")
```

### استفاده از PenetrationTester

```python
from cloud.services.user_management.app.security import PenetrationTester

# ایجاد tester
tester = PenetrationTester("https://api.example.com")

# اجرای تست‌های خاص
await tester.test_authentication()
await tester.test_authorization()
await tester.test_sql_injection()

# تولید گزارش
report = tester.generate_report()
```

---

## بهترین روش‌ها

### 1. OAuth 2.0 / OIDC
- استفاده از state parameter برای CSRF protection
- بررسی expiration tokens
- استفاده از refresh tokens
- Secure storage برای client secrets

### 2. RBAC
- Principle of least privilege
- بررسی مجوزها در هر endpoint
- بررسی دسترسی به منابع خاص
- به‌روزرسانی نقش‌ها و مجوزها

### 3. Audit Logging
- ثبت همه دسترسی‌ها
- ثبت تغییرات مهم
- Retention policy مناسب
- بررسی دوره‌ای logs

### 4. Data Anonymization
- انتخاب سطح مناسب anonymization
- بررسی k-anonymity
- حفظ utility داده
- رعایت GDPR

### 5. Penetration Testing
- اجرای دوره‌ای (سالانه)
- قبل از هر release مهم
- استفاده از automated tools
- بررسی manual برای موارد خاص

---

**آخرین به‌روزرسانی:** 2024

