"""
Feature Store
پیاده‌سازی Feature Store برای مدیریت ویژگی‌های مشترک
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import hashlib
from loguru import logger
import numpy as np
import pandas as pd
from pathlib import Path


# ============================================================================
# Types
# ============================================================================

@dataclass
class Feature:
    """ویژگی"""
    name: str
    dtype: str
    description: str
    created_at: datetime
    version: str
    tags: List[str]
    
    def to_dict(self) -> Dict:
        """تبدیل به dictionary"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Feature':
        """ایجاد از dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class FeatureSet:
    """مجموعه ویژگی‌ها"""
    name: str
    features: List[str]
    description: str
    created_at: datetime
    version: str
    
    def to_dict(self) -> Dict:
        """تبدیل به dictionary"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FeatureSet':
        """ایجاد از dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


# ============================================================================
# Feature Store Manager
# ============================================================================

class FeatureStore:
    """مدیریت Feature Store"""
    
    def __init__(self, store_path: str = "feature_store"):
        """
        مقداردهی اولیه
        
        Args:
            store_path: مسیر ذخیره
        """
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        self.features: Dict[str, Feature] = {}
        self.feature_sets: Dict[str, FeatureSet] = {}
        self.feature_data: Dict[str, np.ndarray] = {}
        
        self.metadata_file = self.store_path / "metadata.json"
        self.load_metadata()
    
    def load_metadata(self):
        """بارگذاری metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    
                    # Load features
                    for name, feature_data in data.get("features", {}).items():
                        self.features[name] = Feature.from_dict(feature_data)
                    
                    # Load feature sets
                    for name, set_data in data.get("feature_sets", {}).items():
                        self.feature_sets[name] = FeatureSet.from_dict(set_data)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
    
    def save_metadata(self):
        """ذخیره metadata"""
        try:
            data = {
                "features": {
                    name: feature.to_dict()
                    for name, feature in self.features.items()
                },
                "feature_sets": {
                    name: feature_set.to_dict()
                    for name, feature_set in self.feature_sets.items()
                }
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def register_feature(
        self,
        name: str,
        dtype: str,
        description: str = "",
        version: str = "1.0.0",
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        ثبت ویژگی
        
        Args:
            name: نام ویژگی
            dtype: نوع داده
            description: توضیحات
            version: نسخه
            tags: تگ‌ها
        
        Returns:
            True در صورت موفقیت
        """
        if name in self.features:
            logger.warning(f"Feature {name} already exists")
            return False
        
        feature = Feature(
            name=name,
            dtype=dtype,
            description=description,
            created_at=datetime.now(),
            version=version,
            tags=tags or []
        )
        
        self.features[name] = feature
        self.save_metadata()
        
        logger.info(f"Registered feature: {name}")
        
        return True
    
    def store_feature_data(
        self,
        feature_name: str,
        data: np.ndarray
    ) -> bool:
        """
        ذخیره داده ویژگی
        
        Args:
            feature_name: نام ویژگی
            data: داده
        
        Returns:
            True در صورت موفقیت
        """
        if feature_name not in self.features:
            logger.error(f"Feature {feature_name} not registered")
            return False
        
        self.feature_data[feature_name] = data
        
        # Save to disk
        feature_file = self.store_path / f"{feature_name}.npy"
        np.save(feature_file, data)
        
        logger.info(f"Stored data for feature: {feature_name}")
        
        return True
    
    def get_feature_data(
        self,
        feature_name: str
    ) -> Optional[np.ndarray]:
        """
        دریافت داده ویژگی
        
        Args:
            feature_name: نام ویژگی
        
        Returns:
            داده یا None
        """
        # Try memory first
        if feature_name in self.feature_data:
            return self.feature_data[feature_name]
        
        # Try disk
        feature_file = self.store_path / f"{feature_name}.npy"
        if feature_file.exists():
            try:
                data = np.load(feature_file)
                self.feature_data[feature_name] = data
                return data
            except Exception as e:
                logger.error(f"Error loading feature data: {e}")
        
        return None
    
    def create_feature_set(
        self,
        name: str,
        features: List[str],
        description: str = "",
        version: str = "1.0.0"
    ) -> bool:
        """
        ایجاد مجموعه ویژگی
        
        Args:
            name: نام مجموعه
            features: لیست نام ویژگی‌ها
            description: توضیحات
            version: نسخه
        
        Returns:
            True در صورت موفقیت
        """
        # Validate features
        for feature_name in features:
            if feature_name not in self.features:
                logger.error(f"Feature {feature_name} not found")
                return False
        
        feature_set = FeatureSet(
            name=name,
            features=features,
            description=description,
            created_at=datetime.now(),
            version=version
        )
        
        self.feature_sets[name] = feature_set
        self.save_metadata()
        
        logger.info(f"Created feature set: {name}")
        
        return True
    
    def get_feature_set_data(
        self,
        feature_set_name: str
    ) -> Optional[pd.DataFrame]:
        """
        دریافت داده مجموعه ویژگی
        
        Args:
            feature_set_name: نام مجموعه
        
        Returns:
            DataFrame یا None
        """
        if feature_set_name not in self.feature_sets:
            return None
        
        feature_set = self.feature_sets[feature_set_name]
        
        # Load all features
        data_dict = {}
        for feature_name in feature_set.features:
            data = self.get_feature_data(feature_name)
            if data is not None:
                data_dict[feature_name] = data
        
        if not data_dict:
            return None
        
        # Create DataFrame
        return pd.DataFrame(data_dict)
    
    def list_features(self, tags: Optional[List[str]] = None) -> List[str]:
        """
        لیست ویژگی‌ها
        
        Args:
            tags: فیلتر بر اساس تگ
        
        Returns:
            لیست نام ویژگی‌ها
        """
        if tags is None:
            return list(self.features.keys())
        
        result = []
        for name, feature in self.features.items():
            if any(tag in feature.tags for tag in tags):
                result.append(name)
        
        return result


# Singleton instance
_feature_store: Optional[FeatureStore] = None


def get_feature_store() -> FeatureStore:
    """دریافت instance feature store"""
    global _feature_store
    if _feature_store is None:
        _feature_store = FeatureStore()
    return _feature_store

