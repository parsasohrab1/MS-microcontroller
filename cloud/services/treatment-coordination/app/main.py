"""
Treatment Coordination Service
سرویس هماهنگی چند نوع درمان همزمان
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import asyncio
from loguru import logger

from .coordination_engine import TreatmentCoordinator
from .models import TreatmentType, TreatmentParams, TreatmentPlan

app = FastAPI(
    title="Treatment Coordination Service",
    description="هماهنگی چند نوع درمان همزمان",
    version="1.0.0"
)

# Coordinator instance
coordinator = TreatmentCoordinator()


class TreatmentRequest(BaseModel):
    """درخواست درمان"""
    patient_id: str
    treatment_type: TreatmentType
    params: Dict[str, float]
    priority: int = 0  # 0=normal, 1=high, 2=critical


class CoordinationRequest(BaseModel):
    """درخواست هماهنگی درمان‌ها"""
    patient_id: str
    treatments: List[TreatmentRequest]
    prediction_data: Optional[Dict] = None


@app.post("/coordinate")
async def coordinate_treatments(request: CoordinationRequest):
    """
    هماهنگی چند نوع درمان
    
    Args:
        request: درخواست هماهنگی
    
    Returns:
        برنامه درمان هماهنگ شده
    """
    try:
        plan = coordinator.coordinate_treatments(
            patient_id=request.patient_id,
            treatments=[t.dict() for t in request.treatments],
            prediction_data=request.prediction_data
        )
        
        return {
            "status": "success",
            "plan": plan.dict(),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Coordination error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/plan/{patient_id}")
async def get_current_plan(patient_id: str):
    """دریافت برنامه درمان فعلی بیمار"""
    plan = coordinator.get_current_plan(patient_id)
    
    if plan is None:
        raise HTTPException(status_code=404, detail="No active plan found")
    
    return plan.dict()


@app.post("/plan/{patient_id}/update")
async def update_plan(patient_id: str, new_plan: TreatmentPlan):
    """به‌روزرسانی برنامه درمان"""
    coordinator.update_plan(patient_id, new_plan)
    return {"status": "updated"}


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Treatment Coordination",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)

