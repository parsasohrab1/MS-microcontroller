"""
Integration Service
سرویس یکپارچه‌سازی با پلتفرم‌های سلامت و سیستم‌های بیمارستانی
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from loguru import logger

from .health_platforms import (
    HealthPlatformsIntegration,
    HealthPlatform,
    HealthData
)
from .hl7_fhir import FHIRClient

app = FastAPI(
    title="Integration Service",
    description="یکپارچه‌سازی با پلتفرم‌های سلامت و سیستم‌های بیمارستانی",
    version="1.0.0"
)

# Instances
health_integration = HealthPlatformsIntegration()
fhir_client = FHIRClient()


class AuthorizeRequest(BaseModel):
    """درخواست احراز هویت"""
    platform: HealthPlatform
    auth_token: str


class SyncRequest(BaseModel):
    """درخواست همگام‌سازی"""
    watch_type: str
    data: List[Dict]


class FHIRExportRequest(BaseModel):
    """درخواست Export به FHIR"""
    patient_id: str
    data: Dict


@app.post("/health/authorize")
async def authorize_health_platform(
    user_id: str,
    request: AuthorizeRequest
):
    """احراز هویت پلتفرم سلامت"""
    try:
        if request.platform == HealthPlatform.APPLE_HEALTH:
            success = await health_integration.authorize_apple_health(
                user_id, request.auth_token
            )
        elif request.platform == HealthPlatform.GOOGLE_FIT:
            success = await health_integration.authorize_google_fit(
                user_id, request.auth_token
            )
        else:
            raise HTTPException(400, "Unsupported platform")
        
        if success:
            return {"status": "authorized", "platform": request.platform.value}
        else:
            raise HTTPException(500, "Authorization failed")
    
    except Exception as e:
        logger.error(f"Authorization error: {e}")
        raise HTTPException(500, str(e))


@app.get("/health/data")
async def get_health_data(
    user_id: str,
    platform: HealthPlatform,
    data_type: str,
    start_date: datetime,
    end_date: datetime
) -> List[HealthData]:
    """دریافت داده از پلتفرم سلامت"""
    try:
        if platform == HealthPlatform.GOOGLE_FIT:
            data = await health_integration.read_google_fit_data(
                user_id, data_type, start_date, end_date
            )
        elif platform == HealthPlatform.APPLE_HEALTH:
            data = await health_integration.read_apple_health_data(
                user_id, data_type, start_date, end_date
            )
        else:
            raise HTTPException(400, "Unsupported platform")
        
        return data
    
    except Exception as e:
        logger.error(f"Error reading health data: {e}")
        raise HTTPException(500, str(e))


@app.post("/smartwatch/sync")
async def sync_smartwatch(
    user_id: str,
    request: SyncRequest
):
    """همگام‌سازی داده از smartwatch"""
    try:
        success = await health_integration.sync_smartwatch_data(
            user_id, request.watch_type, request.data
        )
        
        if success:
            return {"status": "synced", "data_points": len(request.data)}
        else:
            raise HTTPException(500, "Sync failed")
    
    except Exception as e:
        logger.error(f"Sync error: {e}")
        raise HTTPException(500, str(e))


@app.post("/fhir/export")
async def export_to_fhir(request: FHIRExportRequest):
    """Export داده به FHIR"""
    try:
        fhir_resource = await health_integration.export_to_fhir(
            request.patient_id, request.data
        )
        
        return fhir_resource
    
    except Exception as e:
        logger.error(f"FHIR export error: {e}")
        raise HTTPException(500, str(e))


@app.post("/hospital/send")
async def send_to_hospital(
    user_id: str,
    hospital_endpoint: str,
    fhir_data: Dict
):
    """ارسال داده به سیستم بیمارستانی"""
    try:
        success = await health_integration.send_to_hospital_system(
            user_id, hospital_endpoint, fhir_data
        )
        
        if success:
            return {"status": "sent"}
        else:
            raise HTTPException(500, "Failed to send to hospital")
    
    except Exception as e:
        logger.error(f"Error sending to hospital: {e}")
        raise HTTPException(500, str(e))


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Integration Service",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)

