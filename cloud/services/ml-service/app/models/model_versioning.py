"""
Model Versioning
پیاده‌سازی Model Versioning برای نگهداری نسخه‌های مختلف مدل
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json
import os
from pathlib import Path
from loguru import logger
import joblib
import hashlib


# ============================================================================
# Types
# ============================================================================

class ModelStatus(str, Enum):
    """وضعیت مدل"""
    TRAINING = "training"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class ModelVersion:
    """نسخه مدل"""
    version: str
    model_id: str
    model_path: str
    status: ModelStatus
    created_at: datetime
    metrics: Dict[str, float]
    metadata: Dict
    created_by: str
    description: Optional[str] = None
    parent_version: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict:
        """تبدیل به dictionary"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ModelVersion':
        """ایجاد از dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['status'] = ModelStatus(data['status'])
        return cls(**data)


# ============================================================================
# Model Version Manager
# ============================================================================

class ModelVersionManager:
    """مدیریت نسخه‌های مدل"""
    
    def __init__(self, model_store_path: str = "models"):
        """
        مقداردهی اولیه
        
        Args:
            model_store_path: مسیر ذخیره مدل‌ها
        """
        self.model_store_path = Path(model_store_path)
        self.model_store_path.mkdir(parents=True, exist_ok=True)
        self.versions_file = self.model_store_path / "versions.json"
        self.versions: Dict[str, List[ModelVersion]] = {}
        self.load_versions()
    
    def load_versions(self):
        """بارگذاری نسخه‌ها از فایل"""
        if self.versions_file.exists():
            try:
                with open(self.versions_file, 'r') as f:
                    data = json.load(f)
                    for model_id, versions in data.items():
                        self.versions[model_id] = [
                            ModelVersion.from_dict(v) for v in versions
                        ]
            except Exception as e:
                logger.error(f"Error loading versions: {e}")
                self.versions = {}
    
    def save_versions(self):
        """ذخیره نسخه‌ها در فایل"""
        try:
            data = {}
            for model_id, versions in self.versions.items():
                data[model_id] = [v.to_dict() for v in versions]
            
            with open(self.versions_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving versions: {e}")
    
    def register_model(
        self,
        model_id: str,
        model: any,
        metrics: Dict[str, float],
        metadata: Dict,
        created_by: str,
        description: Optional[str] = None,
        parent_version: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        ثبت مدل جدید
        
        Args:
            model_id: شناسه مدل
            model: مدل
            metrics: متریک‌های مدل
            metadata: metadata مدل
            created_by: ایجادکننده
            description: توضیحات
            parent_version: نسخه والد
            tags: تگ‌ها
        
        Returns:
            نسخه مدل
        """
        # Generate version
        version = self._generate_version(model_id)
        
        # Save model
        model_path = self._save_model(model_id, version, model)
        
        # Create version record
        model_version = ModelVersion(
            version=version,
            model_id=model_id,
            model_path=str(model_path),
            status=ModelStatus.STAGING,
            created_at=datetime.now(),
            metrics=metrics,
            metadata=metadata,
            created_by=created_by,
            description=description,
            parent_version=parent_version,
            tags=tags or []
        )
        
        # Add to versions
        if model_id not in self.versions:
            self.versions[model_id] = []
        
        self.versions[model_id].append(model_version)
        self.save_versions()
        
        logger.info(f"Registered model {model_id} version {version}")
        
        return version
    
    def get_model(self, model_id: str, version: Optional[str] = None) -> Optional[any]:
        """
        دریافت مدل
        
        Args:
            model_id: شناسه مدل
            version: نسخه (None برای آخرین نسخه production)
        
        Returns:
            مدل
        """
        if model_id not in self.versions:
            return None
        
        versions = self.versions[model_id]
        
        if version:
            # Get specific version
            model_version = next((v for v in versions if v.version == version), None)
        else:
            # Get latest production version
            production_versions = [
                v for v in versions
                if v.status == ModelStatus.PRODUCTION
            ]
            if not production_versions:
                return None
            model_version = max(production_versions, key=lambda v: v.created_at)
        
        if not model_version:
            return None
        
        # Load model
        return self._load_model(model_version.model_path)
    
    def promote_to_production(
        self,
        model_id: str,
        version: str
    ) -> bool:
        """
        ارتقا مدل به production
        
        Args:
            model_id: شناسه مدل
            version: نسخه
        
        Returns:
            True در صورت موفقیت
        """
        if model_id not in self.versions:
            return False
        
        versions = self.versions[model_id]
        model_version = next((v for v in versions if v.version == version), None)
        
        if not model_version:
            return False
        
        # Demote current production version
        for v in versions:
            if v.status == ModelStatus.PRODUCTION and v.version != version:
                v.status = ModelStatus.DEPRECATED
        
        # Promote new version
        model_version.status = ModelStatus.PRODUCTION
        self.save_versions()
        
        logger.info(f"Promoted model {model_id} version {version} to production")
        
        return True
    
    def rollback(
        self,
        model_id: str,
        target_version: str
    ) -> bool:
        """
        Rollback به نسخه قبلی
        
        Args:
            model_id: شناسه مدل
            target_version: نسخه هدف
        
        Returns:
            True در صورت موفقیت
        """
        return self.promote_to_production(model_id, target_version)
    
    def get_versions(
        self,
        model_id: str,
        status: Optional[ModelStatus] = None
    ) -> List[ModelVersion]:
        """
        دریافت نسخه‌های مدل
        
        Args:
            model_id: شناسه مدل
            status: فیلتر بر اساس وضعیت
        
        Returns:
            لیست نسخه‌ها
        """
        if model_id not in self.versions:
            return []
        
        versions = self.versions[model_id]
        
        if status:
            versions = [v for v in versions if v.status == status]
        
        return sorted(versions, key=lambda v: v.created_at, reverse=True)
    
    def compare_versions(
        self,
        model_id: str,
        version1: str,
        version2: str
    ) -> Dict:
        """
        مقایسه دو نسخه
        
        Args:
            model_id: شناسه مدل
            version1: نسخه اول
            version2: نسخه دوم
        
        Returns:
            نتایج مقایسه
        """
        versions = self.versions.get(model_id, [])
        v1 = next((v for v in versions if v.version == version1), None)
        v2 = next((v for v in versions if v.version == version2), None)
        
        if not v1 or not v2:
            return {}
        
        comparison = {
            "version1": v1.to_dict(),
            "version2": v2.to_dict(),
            "metrics_diff": {},
            "metadata_diff": {}
        }
        
        # Compare metrics
        for key in set(v1.metrics.keys()) | set(v2.metrics.keys()):
            val1 = v1.metrics.get(key, 0)
            val2 = v2.metrics.get(key, 0)
            comparison["metrics_diff"][key] = val2 - val1
        
        return comparison
    
    def _generate_version(self, model_id: str) -> str:
        """تولید نسخه جدید"""
        if model_id not in self.versions:
            return "1.0.0"
        
        versions = self.versions[model_id]
        if not versions:
            return "1.0.0"
        
        # Get latest version
        latest = max(versions, key=lambda v: v.created_at)
        latest_parts = latest.version.split('.')
        
        # Increment patch version
        major, minor, patch = map(int, latest_parts)
        patch += 1
        
        return f"{major}.{minor}.{patch}"
    
    def _save_model(self, model_id: str, version: str, model: any) -> Path:
        """ذخیره مدل"""
        model_dir = self.model_store_path / model_id / version
        model_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = model_dir / "model.pkl"
        joblib.dump(model, model_path)
        
        return model_path
    
    def _load_model(self, model_path: str) -> Optional[any]:
        """بارگذاری مدل"""
        try:
            return joblib.load(model_path)
        except Exception as e:
            logger.error(f"Error loading model from {model_path}: {e}")
            return None


# ============================================================================
# A/B Testing
# ============================================================================

class ABTestManager:
    """مدیریت A/B Testing برای مدل‌ها"""
    
    def __init__(self, version_manager: ModelVersionManager):
        """
        مقداردهی اولیه
        
        Args:
            version_manager: Model version manager
        """
        self.version_manager = version_manager
        self.active_tests: Dict[str, Dict] = {}
    
    def start_ab_test(
        self,
        model_id: str,
        version_a: str,
        version_b: str,
        traffic_split: float = 0.5
    ) -> str:
        """
        شروع A/B test
        
        Args:
            model_id: شناسه مدل
            version_a: نسخه A
            version_b: نسخه B
            traffic_split: تقسیم ترافیک (0.5 = 50/50)
        
        Returns:
            شناسه تست
        """
        test_id = f"{model_id}_{datetime.now().isoformat()}"
        
        self.active_tests[test_id] = {
            "model_id": model_id,
            "version_a": version_a,
            "version_b": version_b,
            "traffic_split": traffic_split,
            "started_at": datetime.now().isoformat(),
            "results": {
                "a": {"requests": 0, "success": 0, "errors": 0},
                "b": {"requests": 0, "success": 0, "errors": 0}
            }
        }
        
        logger.info(f"Started A/B test {test_id}")
        
        return test_id
    
    def get_model_for_request(
        self,
        test_id: str,
        request_id: str
    ) -> Tuple[str, str]:
        """
        دریافت مدل برای request (بر اساس traffic split)
        
        Args:
            test_id: شناسه تست
            request_id: شناسه request
        
        Returns:
            Tuple (version, model_id)
        """
        if test_id not in self.active_tests:
            return None, None
        
        test = self.active_tests[test_id]
        
        # Use hash of request_id for consistent routing
        hash_value = int(hashlib.md5(request_id.encode()).hexdigest(), 16)
        use_b = (hash_value % 100) < (test["traffic_split"] * 100)
        
        version = test["version_b"] if use_b else test["version_a"]
        model_id = test["model_id"]
        
        # Update statistics
        key = "b" if use_b else "a"
        test["results"][key]["requests"] += 1
        
        return version, model_id
    
    def record_result(
        self,
        test_id: str,
        version: str,
        success: bool
    ):
        """
        ثبت نتیجه
        
        Args:
            test_id: شناسه تست
            version: نسخه
            success: موفقیت
        """
        if test_id not in self.active_tests:
            return
        
        test = self.active_tests[test_id]
        key = "b" if version == test["version_b"] else "a"
        
        if success:
            test["results"][key]["success"] += 1
        else:
            test["results"][key]["errors"] += 1
    
    def get_test_results(self, test_id: str) -> Dict:
        """دریافت نتایج تست"""
        if test_id not in self.active_tests:
            return {}
        
        test = self.active_tests[test_id]
        results = test["results"]
        
        # Calculate success rates
        success_rate_a = (
            results["a"]["success"] / results["a"]["requests"]
            if results["a"]["requests"] > 0 else 0
        )
        success_rate_b = (
            results["b"]["success"] / results["b"]["requests"]
            if results["b"]["requests"] > 0 else 0
        )
        
        return {
            "test_id": test_id,
            "version_a": test["version_a"],
            "version_b": test["version_b"],
            "results": {
                "a": {
                    **results["a"],
                    "success_rate": success_rate_a
                },
                "b": {
                    **results["b"],
                    "success_rate": success_rate_b
                }
            },
            "winner": "b" if success_rate_b > success_rate_a else "a"
        }


# Singleton instance
_model_version_manager: Optional[ModelVersionManager] = None
_ab_test_manager: Optional[ABTestManager] = None


def get_model_version_manager() -> ModelVersionManager:
    """دریافت instance model version manager"""
    global _model_version_manager
    if _model_version_manager is None:
        _model_version_manager = ModelVersionManager()
    return _model_version_manager


def get_ab_test_manager() -> ABTestManager:
    """دریافت instance AB test manager"""
    global _ab_test_manager
    if _ab_test_manager is None:
        _ab_test_manager = ABTestManager(get_model_version_manager())
    return _ab_test_manager

