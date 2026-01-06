# راهنمای استفاده از Redis (Caching, Session, Rate Limiting)

## مقدمه

این راهنما نحوه استفاده از Redis برای کش، مدیریت session و rate limiting را توضیح می‌دهد.

---

## نصب و راه‌اندازی

### 1. نصب Redis

```bash
# با Docker
docker run -d --name redis \
  -p 6379:6379 \
  redis:7-alpine

# یا با docker-compose
docker-compose up -d redis
```

### 2. نصب وابستگی‌ها

```bash
pip install redis>=5.0.0
```

### 3. تنظیم متغیر محیطی

```bash
export REDIS_URL=redis://localhost:6379/0
```

---

## استفاده پایه

### مثال 1: Cache ساده

```python
from shared.redis_client import get_redis_client

redis = get_redis_client()

# ذخیره در cache
redis.set_cache("user:123", {"name": "John", "email": "john@example.com"}, ttl=3600)

# دریافت از cache
user = redis.get_cache("user:123")
print(user)  # {"name": "John", "email": "john@example.com"}

# حذف از cache
redis.delete_cache("user:123")
```

### مثال 2: Cache در FastAPI

```python
from fastapi import FastAPI, Depends
from shared.redis_client import get_redis_client
from sqlalchemy.orm import Session

app = FastAPI()
redis = get_redis_client()

@app.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    # بررسی cache
    cache_key = f"user:{user_id}"
    cached_user = redis.get_cache(cache_key)
    
    if cached_user:
        return cached_user
    
    # دریافت از پایگاه داده
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    user_dict = {
        "id": user.id,
        "name": user.name,
        "email": user.email
    }
    
    # ذخیره در cache
    redis.set_cache(cache_key, user_dict, ttl=3600)
    
    return user_dict
```

---

## Session Management

### مثال 3: مدیریت Session

```python
from shared.redis_client import get_redis_client
import secrets

redis = get_redis_client()

# ایجاد session
session_id = secrets.token_urlsafe(32)
redis.set_session(
    session_id=session_id,
    user_id=123,
    data={"ip": "192.168.1.1", "user_agent": "Mozilla/5.0"},
    ttl=3600  # 1 hour
)

# دریافت session
session = redis.get_session(session_id)
if session:
    user_id = session["user_id"]
    print(f"User ID: {user_id}")

# تمدید session
redis.extend_session(session_id, ttl=7200)  # 2 hours

# حذف session
redis.delete_session(session_id)
```

### مثال 4: Session در FastAPI

```python
from fastapi import FastAPI, Request, Response
from shared.redis_client import get_redis_client
import secrets

app = FastAPI()
redis = get_redis_client()

@app.post("/login")
async def login(response: Response, credentials: dict):
    # احراز هویت...
    user_id = 123
    
    # ایجاد session
    session_id = secrets.token_urlsafe(32)
    redis.set_session(session_id, user_id, ttl=3600)
    
    # تنظیم cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=3600,
        httponly=True,
        secure=True
    )
    
    return {"status": "logged in"}

@app.get("/me")
async def get_current_user(request: Request):
    # دریافت session_id از cookie
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(401, "Not authenticated")
    
    # دریافت session
    session = redis.get_session(session_id)
    if not session:
        raise HTTPException(401, "Session expired")
    
    user_id = session["user_id"]
    # دریافت اطلاعات کاربر...
    return {"user_id": user_id}
```

---

## Rate Limiting

### مثال 5: Rate Limiting ساده

```python
from shared.redis_client import get_redis_client
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()
redis = get_redis_client()

@app.get("/api/data")
async def get_data(request: Request):
    # دریافت IP
    client_ip = request.client.host
    
    # بررسی rate limit
    allowed, remaining, reset_time = redis.check_rate_limit(
        identifier=client_ip,
        max_requests=100,  # 100 درخواست
        window_seconds=3600,  # در 1 ساعت
        action="api_request"
    )
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time)
            }
        )
    
    # پردازش درخواست...
    return {
        "data": "...",
        "rate_limit": {
            "remaining": remaining,
            "reset_time": reset_time
        }
    }
```

### مثال 6: Rate Limiting Middleware

```python
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from shared.redis_client import get_redis_client

redis = get_redis_client()

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # دریافت IP
        client_ip = request.client.host
        
        # بررسی rate limit
        allowed, remaining, reset_time = redis.check_rate_limit(
            identifier=client_ip,
            max_requests=100,
            window_seconds=3600,
            action="api_request"
        )
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(reset_time)
                }
            )
        
        # افزودن headers
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response

app = FastAPI()
app.add_middleware(RateLimitMiddleware)
```

### مثال 7: Rate Limiting بر اساس User ID

```python
@app.post("/api/action")
async def perform_action(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    # Rate limiting بر اساس user_id
    allowed, remaining, reset_time = redis.check_rate_limit(
        identifier=f"user:{current_user.id}",
        max_requests=10,  # 10 action
        window_seconds=60,  # در 1 دقیقه
        action="user_action"
    )
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many actions. Please wait.",
            headers={
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time)
            }
        )
    
    # انجام action...
    return {"status": "success"}
```

---

## Real-time Analytics

### مثال 8: Counter

```python
from shared.redis_client import get_redis_client

redis = get_redis_client()

# افزایش counter
page_views = redis.increment_counter("page_views:today", amount=1, ttl=86400)
api_calls = redis.increment_counter("api_calls:user:123", amount=1, ttl=3600)

# دریافت counter
views = redis.get_counter("page_views:today")
print(f"Page views today: {views}")
```

### مثال 9: Tracking Events

```python
# اضافه کردن به set (برای unique tracking)
redis.add_to_set("active_users:today", "user:123", ttl=86400)
redis.add_to_set("active_users:today", "user:456", ttl=86400)

# دریافت تعداد کاربران فعال
active_users = redis.get_set_members("active_users:today")
print(f"Active users: {len(active_users)}")
```

### مثال 10: Leaderboard

```python
# اضافه کردن به sorted set
redis.add_to_sorted_set(
    "leaderboard:monthly",
    score=1000.5,
    value="user:123",
    ttl=2592000  # 30 days
)

# دریافت top 10
top_users = redis.get_sorted_set_range(
    "leaderboard:monthly",
    start=0,
    end=9,
    reverse=True
)
print(f"Top 10 users: {top_users}")
```

---

## بهترین روش‌ها

### 1. Cache Invalidation

```python
# Pattern-based invalidation
def invalidate_user_cache(user_id: int):
    """باطل کردن cache کاربر"""
    redis.clear_cache_pattern(f"user:{user_id}:*")

# Event-based invalidation
def on_user_updated(user_id: int):
    """هنگام به‌روزرسانی کاربر"""
    invalidate_user_cache(user_id)
    # حذف cache خاص
    redis.delete_cache(f"user:{user_id}")
```

### 2. Cache Warming

```python
def warm_cache():
    """گرم کردن cache"""
    # دریافت کاربران پرکاربرد
    popular_users = get_popular_users()
    
    for user in popular_users:
        user_data = get_user_data(user.id)
        redis.set_cache(f"user:{user.id}", user_data, ttl=3600)
```

### 3. TTL Strategy

```python
# TTL کوتاه برای داده‌های متغیر
redis.set_cache("current_price", price, ttl=60)  # 1 minute

# TTL متوسط برای داده‌های نیمه‌ثابت
redis.set_cache("user:123", user_data, ttl=3600)  # 1 hour

# TTL طولانی برای داده‌های ثابت
redis.set_cache("config:system", config, ttl=86400)  # 1 day
```

---

## مانیتورینگ

### بررسی وضعیت Redis

```python
redis = get_redis_client()
redis._ensure_connection()  # تست اتصال
```

### Metrics

```python
# تعداد کلیدها
# (نیاز به استفاده از INFO command)
```

---

## منابع

- [Redis Documentation](https://redis.io/docs/)
- [Redis Python Client](https://redis-py.readthedocs.io/)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)

---

**آخرین به‌روزرسانی:** 2024

