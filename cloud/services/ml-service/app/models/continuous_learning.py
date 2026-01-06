"""
Continuous Learning
پیاده‌سازی Continuous Learning برای به‌روزرسانی مدل با داده‌های جدید
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from loguru import logger
import joblib


# ============================================================================
# Concept Drift Detection
# ============================================================================

class ConceptDriftDetector:
    """تشخیص Concept Drift"""
    
    def __init__(
        self,
        window_size: int = 1000,
        threshold: float = 0.1
    ):
        """
        مقداردهی اولیه
        
        Args:
            window_size: اندازه window برای مقایسه
            threshold: آستانه برای تشخیص drift
        """
        self.window_size = window_size
        self.threshold = threshold
        self.reference_data: List[np.ndarray] = []
        self.reference_predictions: List[int] = []
    
    def set_reference(
        self,
        data: np.ndarray,
        predictions: np.ndarray
    ):
        """
        تنظیم داده مرجع
        
        Args:
            data: داده مرجع
            predictions: پیش‌بینی‌های مرجع
        """
        self.reference_data = data[-self.window_size:].tolist()
        self.reference_predictions = predictions[-self.window_size:].tolist()
        logger.info(f"Reference set with {len(self.reference_data)} samples")
    
    def detect_drift(
        self,
        new_data: np.ndarray,
        new_predictions: np.ndarray
    ) -> Tuple[bool, float]:
        """
        تشخیص drift
        
        Args:
            new_data: داده جدید
            new_predictions: پیش‌بینی‌های جدید
        
        Returns:
            Tuple (drift_detected, drift_score)
        """
        if len(self.reference_data) == 0:
            logger.warning("No reference data set")
            return False, 0.0
        
        # Compare distributions
        # Method 1: Compare prediction distributions
        ref_dist = np.bincount(self.reference_predictions) / len(self.reference_predictions)
        new_dist = np.bincount(new_predictions) / len(new_predictions)
        
        # Pad to same length
        max_len = max(len(ref_dist), len(new_dist))
        ref_dist = np.pad(ref_dist, (0, max_len - len(ref_dist)))
        new_dist = np.pad(new_dist, (0, max_len - len(new_dist)))
        
        # Calculate KL divergence
        drift_score = np.sum(ref_dist * np.log(ref_dist / (new_dist + 1e-10) + 1e-10))
        
        drift_detected = drift_score > self.threshold
        
        if drift_detected:
            logger.warning(f"Concept drift detected! Score: {drift_score:.4f}")
        
        return drift_detected, drift_score
    
    def update_reference(
        self,
        data: np.ndarray,
        predictions: np.ndarray
    ):
        """به‌روزرسانی داده مرجع"""
        self.set_reference(data, predictions)


# ============================================================================
# Data Quality Assurance
# ============================================================================

class DataQualityChecker:
    """بررسی کیفیت داده"""
    
    def __init__(self):
        """مقداردهی اولیه"""
        self.quality_metrics: Dict[str, List[float]] = {}
    
    def check_quality(
        self,
        data: np.ndarray,
        expected_range: Optional[Tuple[float, float]] = None,
        check_missing: bool = True,
        check_outliers: bool = True
    ) -> Dict[str, any]:
        """
        بررسی کیفیت داده
        
        Args:
            data: داده
            expected_range: محدوده مورد انتظار
            check_missing: بررسی missing values
            check_outliers: بررسی outliers
        
        Returns:
            نتایج بررسی
        """
        results = {
            "valid": True,
            "issues": [],
            "metrics": {}
        }
        
        # Check for missing values
        if check_missing:
            missing_count = np.isnan(data).sum()
            missing_percent = (missing_count / data.size) * 100
            results["metrics"]["missing_percent"] = missing_percent
            
            if missing_percent > 5:
                results["valid"] = False
                results["issues"].append(f"High missing values: {missing_percent:.2f}%")
        
        # Check range
        if expected_range:
            min_val, max_val = expected_range
            out_of_range = np.sum((data < min_val) | (data > max_val))
            out_of_range_percent = (out_of_range / data.size) * 100
            results["metrics"]["out_of_range_percent"] = out_of_range_percent
            
            if out_of_range_percent > 10:
                results["valid"] = False
                results["issues"].append(f"High out-of-range values: {out_of_range_percent:.2f}%")
        
        # Check outliers
        if check_outliers:
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = np.sum((data < lower_bound) | (data > upper_bound))
            outliers_percent = (outliers / data.size) * 100
            results["metrics"]["outliers_percent"] = outliers_percent
            
            if outliers_percent > 5:
                results["issues"].append(f"High outliers: {outliers_percent:.2f}%")
        
        return results


# ============================================================================
# Continuous Learning Manager
# ============================================================================

class ContinuousLearningManager:
    """مدیریت Continuous Learning"""
    
    def __init__(
        self,
        model: any,
        retrain_threshold: float = 0.05,  # 5% performance drop
        min_new_samples: int = 1000,
        retrain_interval_days: int = 7
    ):
        """
        مقداردهی اولیه
        
        Args:
            model: مدل
            retrain_threshold: آستانه برای retrain
            min_new_samples: حداقل نمونه‌های جدید
            retrain_interval_days: فاصله retrain (روز)
        """
        self.model = model
        self.retrain_threshold = retrain_threshold
        self.min_new_samples = min_new_samples
        self.retrain_interval_days = retrain_interval_days
        
        self.drift_detector = ConceptDriftDetector()
        self.quality_checker = DataQualityChecker()
        
        self.new_data: List[np.ndarray] = []
        self.new_labels: List[int] = []
        self.last_retrain: Optional[datetime] = None
        self.baseline_metrics: Dict[str, float] = {}
    
    def add_training_data(
        self,
        data: np.ndarray,
        labels: np.ndarray
    ):
        """
        اضافه کردن داده آموزشی جدید
        
        Args:
            data: داده
            labels: برچسب‌ها
        """
        # Check data quality
        quality_result = self.quality_checker.check_quality(data)
        
        if not quality_result["valid"]:
            logger.warning(f"Data quality issues: {quality_result['issues']}")
            # Still add data, but log warning
            # In production, might want to reject or clean data
        
        self.new_data.extend(data)
        self.new_labels.extend(labels)
        
        logger.info(f"Added {len(data)} new training samples. Total: {len(self.new_data)}")
    
    def should_retrain(self) -> Tuple[bool, str]:
        """
        بررسی نیاز به retrain
        
        Returns:
            Tuple (should_retrain, reason)
        """
        # Check minimum samples
        if len(self.new_data) < self.min_new_samples:
            return False, f"Insufficient new samples: {len(self.new_data)}/{self.min_new_samples}"
        
        # Check time interval
        if self.last_retrain:
            days_since_retrain = (datetime.now() - self.last_retrain).days
            if days_since_retrain < self.retrain_interval_days:
                return False, f"Too soon since last retrain: {days_since_retrain} days"
        
        # Check for concept drift
        if len(self.new_data) >= self.drift_detector.window_size:
            new_data_array = np.array(self.new_data[-self.drift_detector.window_size:])
            new_predictions = self.model.predict(new_data_array)
            
            drift_detected, drift_score = self.drift_detector.detect_drift(
                new_data_array,
                new_predictions
            )
            
            if drift_detected:
                return True, f"Concept drift detected: {drift_score:.4f}"
        
        # Check performance degradation
        if self.baseline_metrics:
            current_metrics = self._evaluate_model()
            performance_drop = (
                self.baseline_metrics.get("accuracy", 1.0) -
                current_metrics.get("accuracy", 0.0)
            )
            
            if performance_drop > self.retrain_threshold:
                return True, f"Performance drop: {performance_drop:.4f}"
        
        return True, "Scheduled retrain"
    
    def retrain_model(
        self,
        all_training_data: np.ndarray,
        all_training_labels: np.ndarray,
        validation_data: Optional[np.ndarray] = None,
        validation_labels: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Retrain مدل
        
        Args:
            all_training_data: تمام داده‌های آموزشی
            all_training_labels: تمام برچسب‌های آموزشی
            validation_data: داده validation
            validation_labels: برچسب‌های validation
        
        Returns:
            متریک‌های مدل جدید
        """
        logger.info("Starting model retraining...")
        
        # Retrain model
        self.model.fit(all_training_data, all_training_labels)
        
        # Evaluate
        if validation_data is not None and validation_labels is not None:
            metrics = self._evaluate_model(validation_data, validation_labels)
        else:
            metrics = self._evaluate_model(all_training_data, all_training_labels)
        
        # Update baseline
        self.baseline_metrics = metrics
        
        # Update drift detector reference
        predictions = self.model.predict(all_training_data[-1000:])
        self.drift_detector.set_reference(
            all_training_data[-1000:],
            predictions
        )
        
        # Clear new data
        self.new_data = []
        self.new_labels = []
        self.last_retrain = datetime.now()
        
        logger.info(f"Model retrained. Metrics: {metrics}")
        
        return metrics
    
    def _evaluate_model(
        self,
        data: Optional[np.ndarray] = None,
        labels: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """ارزیابی مدل"""
        if data is None:
            data = np.array(self.new_data)
        if labels is None:
            labels = np.array(self.new_labels)
        
        if len(data) == 0:
            return {}
        
        predictions = self.model.predict(data)
        
        metrics = {
            "accuracy": accuracy_score(labels, predictions),
            "precision": precision_score(labels, predictions, average='weighted', zero_division=0),
            "recall": recall_score(labels, predictions, average='weighted', zero_division=0),
            "f1": f1_score(labels, predictions, average='weighted', zero_division=0)
        }
        
        return metrics


# Singleton instance
_continuous_learning_manager: Optional[ContinuousLearningManager] = None


def get_continuous_learning_manager(model: any) -> ContinuousLearningManager:
    """دریافت instance continuous learning manager"""
    global _continuous_learning_manager
    if _continuous_learning_manager is None:
        _continuous_learning_manager = ContinuousLearningManager(model)
    return _continuous_learning_manager

