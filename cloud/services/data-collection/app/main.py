"""
Data Collection Service
سرویس جمع‌آوری داده از Gateway و دستگاه‌ها
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from loguru import logger
import asyncio

from app.database import get_db, init_db
from app.models import SensorData, Patient
from app.message_queue import publish_to_queue
from app.validators import validate_sensor_data

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Data Collection Service",
    description="Service for collecting sensor data from devices",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    await init_db()
    logger.info("Data Collection Service started")


# ============================================================================
# Models
# ============================================================================

class SensorDataRequest(BaseModel):
    """درخواست ارسال داده سنسور"""
    patient_id: str
    device_id: str
    timestamp: datetime
    eeg_data: Optional[List[List[float]]] = Field(None, description="EEG data (channels x samples)")
    biomarker_values: Optional[Dict[str, float]] = Field(None, description="Biomarker values")
    physiological_params: Optional[Dict[str, float]] = Field(None, description="Physiological parameters")
    metadata: Optional[Dict] = Field(None, description="Additional metadata")


class SensorDataResponse(BaseModel):
    """پاسخ ارسال داده"""
    success: bool
    data_id: str
    message: str
    timestamp: datetime


class BatchSensorDataRequest(BaseModel):
    """درخواست ارسال دسته‌ای داده"""
    data: List[SensorDataRequest]


# ============================================================================
# Routes
# ============================================================================

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "data-collection"}


@app.post("/data/sensor", response_model=SensorDataResponse)
async def collect_sensor_data(
    request: SensorDataRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """
    جمع‌آوری داده سنسور
    
    Args:
        request: درخواست داده
        background_tasks: Background tasks
        db: Database session
    
    Returns:
        پاسخ
    """
    try:
        # Validate data
        validation_result = validate_sensor_data(request)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sensor data: {validation_result['errors']}"
            )
        
        # Check patient exists
        patient = await db.get(Patient, request.patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Create sensor data record
        sensor_data = SensorData(
            patient_id=request.patient_id,
            device_id=request.device_id,
            timestamp=request.timestamp,
            eeg_data=request.eeg_data,
            biomarker_values=request.biomarker_values,
            physiological_params=request.physiological_params,
            metadata=request.metadata
        )
        
        db.add(sensor_data)
        await db.commit()
        await db.refresh(sensor_data)
        
        # Publish to message queue for processing
        background_tasks.add_task(
            publish_sensor_data,
            sensor_data.id,
            request
        )
        
        logger.info(f"Collected sensor data for patient {request.patient_id}")
        
        return SensorDataResponse(
            success=True,
            data_id=str(sensor_data.id),
            message="Data collected successfully",
            timestamp=datetime.now()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error collecting sensor data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/data/sensor/batch", response_model=List[SensorDataResponse])
async def collect_batch_sensor_data(
    request: BatchSensorDataRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """
    جمع‌آوری دسته‌ای داده سنسور
    
    Args:
        request: درخواست دسته‌ای
        background_tasks: Background tasks
        db: Database session
    
    Returns:
        لیست پاسخ‌ها
    """
    results = []
    
    for data_request in request.data:
        try:
            response = await collect_sensor_data(data_request, background_tasks, db)
            results.append(response)
        except Exception as e:
            logger.error(f"Error processing batch item: {e}")
            results.append(SensorDataResponse(
                success=False,
                data_id="",
                message=str(e),
                timestamp=datetime.now()
            ))
    
    return results


@app.get("/data/sensor/{patient_id}")
async def get_sensor_data(
    patient_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    db=Depends(get_db)
):
    """
    دریافت داده سنسور بیمار
    
    Args:
        patient_id: شناسه بیمار
        start_time: زمان شروع
        end_time: زمان پایان
        limit: حداکثر تعداد
        db: Database session
    
    Returns:
        لیست داده‌ها
    """
    try:
        query = db.query(SensorData).filter(SensorData.patient_id == patient_id)
        
        if start_time:
            query = query.filter(SensorData.timestamp >= start_time)
        if end_time:
            query = query.filter(SensorData.timestamp <= end_time)
        
        query = query.order_by(SensorData.timestamp.desc()).limit(limit)
        
        data = await query.all()
        
        return {
            "patient_id": patient_id,
            "count": len(data),
            "data": [
                {
                    "id": str(d.id),
                    "device_id": d.device_id,
                    "timestamp": d.timestamp.isoformat(),
                    "biomarker_values": d.biomarker_values,
                    "physiological_params": d.physiological_params
                }
                for d in data
            ]
        }
    
    except Exception as e:
        logger.error(f"Error getting sensor data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/sensor/stats/{patient_id}")
async def get_sensor_stats(
    patient_id: str,
    days: int = 7,
    db=Depends(get_db)
):
    """
    دریافت آمار داده سنسور
    
    Args:
        patient_id: شناسه بیمار
        days: تعداد روز
        db: Database session
    
    Returns:
        آمار
    """
    try:
        from datetime import timedelta
        
        start_time = datetime.now() - timedelta(days=days)
        
        query = db.query(SensorData).filter(
            SensorData.patient_id == patient_id,
            SensorData.timestamp >= start_time
        )
        
        data = await query.all()
        
        if not data:
            return {
                "patient_id": patient_id,
                "period_days": days,
                "total_records": 0,
                "stats": {}
            }
        
        # Calculate statistics
        stats = {
            "total_records": len(data),
            "devices": list(set(d.device_id for d in data)),
            "date_range": {
                "start": min(d.timestamp for d in data).isoformat(),
                "end": max(d.timestamp for d in data).isoformat()
            }
        }
        
        # Biomarker statistics
        if data[0].biomarker_values:
            biomarker_stats = {}
            for key in data[0].biomarker_values.keys():
                values = [d.biomarker_values.get(key) for d in data if d.biomarker_values and key in d.biomarker_values]
                if values:
                    biomarker_stats[key] = {
                        "mean": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values)
                    }
            stats["biomarker_stats"] = biomarker_stats
        
        return {
            "patient_id": patient_id,
            "period_days": days,
            **stats
        }
    
    except Exception as e:
        logger.error(f"Error getting sensor stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Background Tasks
# ============================================================================

async def publish_sensor_data(data_id: str, request: SensorDataRequest):
    """
    ارسال داده به message queue
    
    Args:
        data_id: شناسه داده
        request: درخواست
    """
    try:
        message = {
            "data_id": data_id,
            "patient_id": request.patient_id,
            "device_id": request.device_id,
            "timestamp": request.timestamp.isoformat(),
            "has_eeg": request.eeg_data is not None,
            "has_biomarkers": request.biomarker_values is not None
        }
        
        await publish_to_queue("sensor_data", message)
        logger.info(f"Published sensor data {data_id} to queue")
    
    except Exception as e:
        logger.error(f"Error publishing sensor data: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

