"""
Application Performance Monitoring (APM)
مانیتورینگ عملکرد با Prometheus
"""

from prometheus_client import Counter, Histogram, Gauge, start_http_server
from functools import wraps
import time
from typing import Callable, Any
from loguru import logger


# ============================================================================
# Prometheus Metrics
# ============================================================================

# HTTP Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Database Metrics
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation', 'table']
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation', 'table']
)

# Business Metrics
active_patients = Gauge(
    'active_patients',
    'Number of active patients'
)

predictions_total = Counter(
    'predictions_total',
    'Total predictions made',
    ['model', 'result']
)

prediction_duration_seconds = Histogram(
    'prediction_duration_seconds',
    'Prediction duration',
    ['model']
)

# System Metrics
memory_usage_bytes = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes',
    ['service']
)

cpu_usage_percent = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage',
    ['service']
)


# ============================================================================
# Decorators
# ============================================================================

def monitor_http_request(endpoint: str = None):
    """
    Decorator برای مانیتورینگ HTTP requests
    
    Args:
        endpoint: نام endpoint
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            method = kwargs.get('method', 'GET')
            endpoint_name = endpoint or func.__name__
            
            start_time = time.time()
            status = '200'
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = '500'
                raise
            finally:
                duration = time.time() - start_time
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint_name,
                    status=status
                ).inc()
                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint_name
                ).observe(duration)
        
        return wrapper
    return decorator


def monitor_database_query(operation: str, table: str):
    """
    Decorator برای مانیتورینگ database queries
    
    Args:
        operation: نوع عملیات (select, insert, update, delete)
        table: نام جدول
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                db_queries_total.labels(
                    operation=operation,
                    table=table
                ).inc()
                db_query_duration_seconds.labels(
                    operation=operation,
                    table=table
                ).observe(duration)
        
        return wrapper
    return decorator


def monitor_prediction(model: str):
    """
    Decorator برای مانیتورینگ predictions
    
    Args:
        model: نام مدل
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = None
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                predictions_total.labels(
                    model=model,
                    result='success' if result else 'failure'
                ).inc()
                prediction_duration_seconds.labels(
                    model=model
                ).observe(duration)
        
        return wrapper
    return decorator


# ============================================================================
# Initialization
# ============================================================================

def start_monitoring(port: int = 9090):
    """
    شروع مانیتورینگ
    
    Args:
        port: پورت برای metrics endpoint
    """
    try:
        start_http_server(port)
        logger.info(f"Prometheus metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")


# ============================================================================
# Helper Functions
# ============================================================================

def update_active_patients(count: int):
    """به‌روزرسانی تعداد active patients"""
    active_patients.set(count)


def update_memory_usage(service: str, bytes_used: int):
    """به‌روزرسانی memory usage"""
    memory_usage_bytes.labels(service=service).set(bytes_used)


def update_cpu_usage(service: str, percent: float):
    """به‌روزرسانی CPU usage"""
    cpu_usage_percent.labels(service=service).set(percent)

