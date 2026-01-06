"""
API Gateway
Gateway اصلی برای همه API ها
"""

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from datetime import datetime

from .versioning import version_middleware, get_version_manager
from .rate_limiting import rate_limit_middleware, get_rate_limiter, RateLimitRule
from .response_compression import CompressionMiddleware
from .graphql.main import app as graphql_app

# ایجاد FastAPI app
app = FastAPI(
    title="MS Neuroplatform API Gateway",
    description="API Gateway برای تمام سرویس‌ها",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # در production محدود کنید
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response Compression
app.add_middleware(CompressionMiddleware, minimum_size=500)

# Rate Limiting
app.middleware("http")(rate_limit_middleware)

# API Versioning
app.middleware("http")(version_middleware)

# Mount GraphQL
app.mount("/graphql", graphql_app)


# ============================================================================
# تنظیمات Rate Limiting
# ============================================================================

@app.on_event("startup")
async def setup_rate_limiting():
    """تنظیم rate limiting در startup"""
    rate_limiter = get_rate_limiter()
    
    # تنظیم قوانین برای endpoints مختلف
    rate_limiter.set_rule(
        "/api/v1/auth/login",
        RateLimitRule(
            requests_per_minute=5,
            requests_per_hour=20,
            requests_per_day=100
        )
    )
    
    rate_limiter.set_rule(
        "/api/v1/data/",
        RateLimitRule(
            requests_per_minute=100,
            requests_per_hour=5000,
            requests_per_day=50000
        )
    )
    
    rate_limiter.set_rule(
        "/api/v1/ml/predict",
        RateLimitRule(
            requests_per_minute=30,
            requests_per_hour=1000,
            requests_per_day=10000
        )
    )
    
    # شروع cleanup task
    import asyncio
    asyncio.create_task(rate_limiter.start_cleanup_task())
    
    logger.info("Rate limiting configured")


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "API Gateway",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# API Info
# ============================================================================

@app.get("/api/info")
async def api_info(request: Request):
    """اطلاعات API"""
    version_manager = get_version_manager()
    version = version_manager.get_version_from_header(request)
    
    return {
        "api_name": "MS Neuroplatform API",
        "version": version,
        "supported_versions": version_manager.supported_versions,
        "default_version": version_manager.default_version,
        "deprecated_versions": version_manager.deprecated_versions,
        "endpoints": {
            "rest": "/api/v1/",
            "graphql": "/graphql",
            "health": "/health"
        }
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handler برای 404"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"Endpoint {request.url.path} not found",
            "available_endpoints": [
                "/api/v1/",
                "/graphql",
                "/health"
            ]
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handler برای 500"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An internal error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

