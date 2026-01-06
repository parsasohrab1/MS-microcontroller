"""
ML Service Main
سرویس ML برای پیش‌بینی و مدل‌های ML
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import numpy as np
from loguru import logger

from app.models.advanced_models import AdvancedModelManager
from app.models.model_versioning import get_model_version_manager, get_ab_test_manager
from app.models.continuous_learning import get_continuous_learning_manager
from app.data.feature_store import get_feature_store
from app.data.data_pipeline import DataPipeline

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="ML Service",
    description="Machine Learning Service for MS Neuroplatform",
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

class PredictionRequest(BaseModel):
    """درخواست پیش‌بینی"""
    patient_id: str
    features: List[float]
    model_id: Optional[str] = None


class PredictionResponse(BaseModel):
    """پاسخ پیش‌بینی"""
    prediction: int
    confidence: float
    model_version: str
    inference_time_ms: float


class ModelVersionRequest(BaseModel):
    """درخواست ثبت مدل"""
    model_id: str
    metrics: Dict[str, float]
    metadata: Dict
    created_by: str
    description: Optional[str] = None


# ============================================================================
# Managers
# ============================================================================

model_manager = AdvancedModelManager()
version_manager = get_model_version_manager()
ab_test_manager = get_ab_test_manager()
feature_store = get_feature_store()

# ============================================================================
# Routes
# ============================================================================

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    پیش‌بینی
    
    Args:
        request: درخواست پیش‌بینی
    
    Returns:
        پاسخ پیش‌بینی
    """
    try:
        # Get model
        model_id = request.model_id or "default"
        model = model_manager.get_model(model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        # Prepare input
        input_data = np.array(request.features).reshape(1, -1)
        
        # Predict
        import time
        start_time = time.time()
        prediction = model_manager.predict(model_id, input_data)
        inference_time = (time.time() - start_time) * 1000  # ms
        
        # Get model version
        model_version = version_manager.get_versions(model_id)
        current_version = model_version[0].version if model_version else "unknown"
        
        return PredictionResponse(
            prediction=int(np.argmax(prediction)),
            confidence=float(np.max(prediction)),
            model_version=current_version,
            inference_time_ms=inference_time
        )
    
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/models/register")
async def register_model(request: ModelVersionRequest):
    """
    ثبت مدل جدید
    
    Args:
        request: درخواست ثبت مدل
    
    Returns:
        نسخه مدل
    """
    try:
        # TODO: Load actual model from request
        # For now, we'll just register metadata
        
        version = version_manager.register_model(
            model_id=request.model_id,
            model=None,  # TODO: Load model
            metrics=request.metrics,
            metadata=request.metadata,
            created_by=request.created_by,
            description=request.description
        )
        
        return {"version": version, "model_id": request.model_id}
    
    except Exception as e:
        logger.error(f"Model registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models/{model_id}/versions")
async def get_model_versions(model_id: str):
    """دریافت نسخه‌های مدل"""
    versions = version_manager.get_versions(model_id)
    return {
        "model_id": model_id,
        "versions": [v.to_dict() for v in versions]
    }


@app.post("/models/{model_id}/promote/{version}")
async def promote_model(model_id: str, version: str):
    """ارتقا مدل به production"""
    success = version_manager.promote_to_production(model_id, version)
    if not success:
        raise HTTPException(status_code=404, detail="Model or version not found")
    return {"success": True}


@app.post("/ab-test/start")
async def start_ab_test(
    model_id: str,
    version_a: str,
    version_b: str,
    traffic_split: float = 0.5
):
    """شروع A/B test"""
    test_id = ab_test_manager.start_ab_test(
        model_id=model_id,
        version_a=version_a,
        version_b=version_b,
        traffic_split=traffic_split
    )
    return {"test_id": test_id}


@app.get("/ab-test/{test_id}/results")
async def get_ab_test_results(test_id: str):
    """دریافت نتایج A/B test"""
    results = ab_test_manager.get_test_results(test_id)
    if not results:
        raise HTTPException(status_code=404, detail="Test not found")
    return results


@app.get("/features")
async def list_features(tags: Optional[List[str]] = None):
    """لیست ویژگی‌ها"""
    features = feature_store.list_features(tags=tags)
    return {"features": features}


@app.get("/pipeline/quality")
async def get_pipeline_quality(hours: int = 24):
    """دریافت متریک‌های کیفیت pipeline"""
    # TODO: Get from actual pipeline
    return {"metrics": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

