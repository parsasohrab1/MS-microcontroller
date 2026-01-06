"""
Analytics Service
سرویس تحلیل و گزارش‌گیری
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from loguru import logger
import numpy as np
import pandas as pd

from app.database import get_db
from app.cache import get_from_cache, set_to_cache
from app.statistics import calculate_statistics, generate_report

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Analytics Service",
    description="Service for analytics and reporting",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Models
# ============================================================================

class AnalyticsRequest(BaseModel):
    """درخواست تحلیل"""
    patient_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metrics: Optional[List[str]] = None


class AnalyticsResponse(BaseModel):
    """پاسخ تحلیل"""
    patient_id: Optional[str]
    period: Dict[str, str]
    statistics: Dict
    trends: Dict
    generated_at: datetime


class ReportRequest(BaseModel):
    """درخواست گزارش"""
    patient_id: str
    report_type: str  # "daily", "weekly", "monthly"
    format: str = "json"  # "json", "pdf", "excel"


# ============================================================================
# Routes
# ============================================================================

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "analytics"}


@app.post("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    request: AnalyticsRequest,
    db=Depends(get_db)
):
    """
    دریافت تحلیل‌ها
    
    Args:
        request: درخواست
        db: Database session
    
    Returns:
        تحلیل‌ها
    """
    try:
        # Check cache
        cache_key = f"analytics:{request.patient_id}:{request.start_date}:{request.end_date}"
        cached_result = await get_from_cache(cache_key)
        if cached_result:
            return AnalyticsResponse(**cached_result)
        
        # Calculate statistics
        stats = await calculate_statistics(
            patient_id=request.patient_id,
            start_date=request.start_date,
            end_date=request.end_date,
            metrics=request.metrics,
            db=db
        )
        
        # Calculate trends
        trends = await calculate_trends(
            patient_id=request.patient_id,
            start_date=request.start_date,
            end_date=request.end_date,
            db=db
        )
        
        # Prepare response
        response = AnalyticsResponse(
            patient_id=request.patient_id,
            period={
                "start": request.start_date.isoformat() if request.start_date else None,
                "end": request.end_date.isoformat() if request.end_date else None
            },
            statistics=stats,
            trends=trends,
            generated_at=datetime.now()
        )
        
        # Cache result
        await set_to_cache(cache_key, response.dict(), ttl=3600)
        
        return response
    
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/report")
async def generate_report_endpoint(
    request: ReportRequest,
    db=Depends(get_db)
):
    """
    تولید گزارش
    
    Args:
        request: درخواست
        db: Database session
    
    Returns:
        گزارش
    """
    try:
        # Generate report
        report = await generate_report(
            patient_id=request.patient_id,
            report_type=request.report_type,
            format=request.format,
            db=db
        )
        
        return report
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/patient/{patient_id}/summary")
async def get_patient_summary(
    patient_id: str,
    days: int = 30,
    db=Depends(get_db)
):
    """
    دریافت خلاصه بیمار
    
    Args:
        patient_id: شناسه بیمار
        days: تعداد روز
        db: Database session
    
    Returns:
        خلاصه
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get analytics
        request = AnalyticsRequest(
            patient_id=patient_id,
            start_date=start_date,
            end_date=end_date
        )
        
        analytics = await get_analytics(request, db)
        
        # Create summary
        summary = {
            "patient_id": patient_id,
            "period_days": days,
            "key_metrics": {
                "total_predictions": analytics.statistics.get("total_predictions", 0),
                "attack_predictions": analytics.statistics.get("attack_predictions", 0),
                "avg_confidence": analytics.statistics.get("avg_confidence", 0),
            },
            "trends": analytics.trends,
            "generated_at": analytics.generated_at.isoformat()
        }
        
        return summary
    
    except Exception as e:
        logger.error(f"Error getting patient summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def calculate_trends(
    patient_id: Optional[str],
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    db
) -> Dict:
    """
    محاسبه روندها
    
    Args:
        patient_id: شناسه بیمار
        start_date: تاریخ شروع
        end_date: تاریخ پایان
        db: Database session
    
    Returns:
        روندها
    """
    # TODO: پیاده‌سازی محاسبه روندها
    # این نیاز به داده‌های تاریخی دارد
    
    return {
        "attack_frequency": "stable",
        "confidence_trend": "increasing",
        "biomarker_trends": {}
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

