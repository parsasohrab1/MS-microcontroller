"""
Data Pipeline
پیاده‌سازی Data Pipeline برای ETL automated, Data validation, Data quality monitoring
"""

from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from loguru import logger
from enum import Enum


# ============================================================================
# Types
# ============================================================================

class PipelineStage(str, Enum):
    """مراحل pipeline"""
    EXTRACT = "extract"
    TRANSFORM = "transform"
    LOAD = "load"
    VALIDATE = "validate"


@dataclass
class PipelineStep:
    """مرحله pipeline"""
    name: str
    stage: PipelineStage
    function: Callable
    dependencies: List[str]
    enabled: bool = True


@dataclass
class DataQualityMetric:
    """متریک کیفیت داده"""
    name: str
    value: float
    threshold: float
    status: str  # "pass", "warning", "fail"
    timestamp: datetime


# ============================================================================
# Data Validators
# ============================================================================

class DataValidator:
    """اعتبارسنجی داده"""
    
    @staticmethod
    def validate_range(
        data: np.ndarray,
        min_val: float,
        max_val: float
    ) -> Dict[str, Any]:
        """
        اعتبارسنجی محدوده
        
        Args:
            data: داده
            min_val: حداقل
            max_val: حداکثر
        
        Returns:
            نتایج اعتبارسنجی
        """
        out_of_range = np.sum((data < min_val) | (data > max_val))
        total = len(data)
        percent = (out_of_range / total) * 100 if total > 0 else 0
        
        return {
            "valid": percent < 5,  # کمتر از 5% out of range
            "out_of_range_count": int(out_of_range),
            "out_of_range_percent": percent,
            "total": total
        }
    
    @staticmethod
    def validate_missing(
        data: np.ndarray
    ) -> Dict[str, Any]:
        """
        اعتبارسنجی missing values
        
        Args:
            data: داده
        
        Returns:
            نتایج اعتبارسنجی
        """
        missing = np.isnan(data).sum()
        total = data.size
        percent = (missing / total) * 100 if total > 0 else 0
        
        return {
            "valid": percent < 10,  # کمتر از 10% missing
            "missing_count": int(missing),
            "missing_percent": percent,
            "total": total
        }
    
    @staticmethod
    def validate_outliers(
        data: np.ndarray,
        method: str = "iqr"
    ) -> Dict[str, Any]:
        """
        اعتبارسنجی outliers
        
        Args:
            data: داده
            method: روش (iqr, zscore)
        
        Returns:
            نتایج اعتبارسنجی
        """
        if method == "iqr":
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            
            outliers = np.sum((data < lower) | (data > upper))
        else:  # zscore
            mean = np.mean(data)
            std = np.std(data)
            z_scores = np.abs((data - mean) / std)
            outliers = np.sum(z_scores > 3)
        
        total = len(data)
        percent = (outliers / total) * 100 if total > 0 else 0
        
        return {
            "valid": percent < 5,  # کمتر از 5% outliers
            "outlier_count": int(outliers),
            "outlier_percent": percent,
            "total": total
        }


# ============================================================================
# Data Pipeline Manager
# ============================================================================

class DataPipeline:
    """مدیریت Data Pipeline"""
    
    def __init__(self, name: str):
        """
        مقداردهی اولیه
        
        Args:
            name: نام pipeline
        """
        self.name = name
        self.steps: List[PipelineStep] = []
        self.quality_metrics: List[DataQualityMetric] = []
        self.execution_history: List[Dict] = []
    
    def add_step(
        self,
        name: str,
        stage: PipelineStage,
        function: Callable,
        dependencies: Optional[List[str]] = None,
        enabled: bool = True
    ):
        """
        اضافه کردن مرحله
        
        Args:
            name: نام مرحله
            stage: نوع مرحله
            function: تابع
            dependencies: وابستگی‌ها
            enabled: فعال/غیرفعال
        """
        step = PipelineStep(
            name=name,
            stage=stage,
            function=function,
            dependencies=dependencies or [],
            enabled=enabled
        )
        
        self.steps.append(step)
        logger.info(f"Added step {name} to pipeline {self.name}")
    
    def execute(
        self,
        input_data: Any,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        اجرای pipeline
        
        Args:
            input_data: داده ورودی
            validate: اعتبارسنجی
        
        Returns:
            نتایج اجرا
        """
        start_time = datetime.now()
        logger.info(f"Starting pipeline {self.name}")
        
        current_data = input_data
        step_results = {}
        
        # Sort steps by dependencies
        sorted_steps = self._topological_sort()
        
        # Execute steps
        for step in sorted_steps:
            if not step.enabled:
                logger.info(f"Skipping disabled step: {step.name}")
                continue
            
            try:
                logger.info(f"Executing step: {step.name} ({step.stage.value})")
                
                # Check dependencies
                for dep in step.dependencies:
                    if dep not in step_results:
                        raise ValueError(f"Dependency {dep} not found")
                
                # Execute
                result = step.function(current_data, step_results)
                step_results[step.name] = result
                current_data = result
                
            except Exception as e:
                logger.error(f"Error in step {step.name}: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "failed_step": step.name,
                    "step_results": step_results
                }
        
        # Validation
        validation_results = {}
        if validate:
            validation_results = self._validate_data(current_data)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        execution_result = {
            "success": True,
            "pipeline": self.name,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "step_results": step_results,
            "validation": validation_results,
            "output_data": current_data
        }
        
        self.execution_history.append(execution_result)
        logger.info(f"Pipeline {self.name} completed in {duration:.2f}s")
        
        return execution_result
    
    def _topological_sort(self) -> List[PipelineStep]:
        """مرتب‌سازی توپولوژیکی بر اساس dependencies"""
        # Simple implementation - assumes no cycles
        sorted_steps = []
        remaining = self.steps.copy()
        
        while remaining:
            # Find steps with no unsatisfied dependencies
            ready = [
                step for step in remaining
                if all(
                    dep in [s.name for s in sorted_steps]
                    for dep in step.dependencies
                )
            ]
            
            if not ready:
                # Cycle detected or missing dependency
                logger.warning("Could not resolve dependencies, using original order")
                return self.steps
            
            sorted_steps.extend(ready)
            remaining = [s for s in remaining if s not in ready]
        
        return sorted_steps
    
    def _validate_data(self, data: Any) -> Dict[str, Any]:
        """اعتبارسنجی داده"""
        validator = DataValidator()
        results = {}
        
        if isinstance(data, np.ndarray):
            # Validate array
            results["missing"] = validator.validate_missing(data)
            results["outliers"] = validator.validate_outliers(data)
            
            # Store metrics
            self.quality_metrics.append(DataQualityMetric(
                name="missing_percent",
                value=results["missing"]["missing_percent"],
                threshold=10.0,
                status="pass" if results["missing"]["valid"] else "fail",
                timestamp=datetime.now()
            ))
        
        elif isinstance(data, pd.DataFrame):
            # Validate DataFrame
            for column in data.columns:
                col_data = data[column].values
                results[column] = {
                    "missing": validator.validate_missing(col_data),
                    "outliers": validator.validate_outliers(col_data)
                }
        
        return results
    
    def get_quality_metrics(
        self,
        hours: int = 24
    ) -> List[DataQualityMetric]:
        """
        دریافت متریک‌های کیفیت
        
        Args:
            hours: تعداد ساعت گذشته
        
        Returns:
            لیست متریک‌ها
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            metric for metric in self.quality_metrics
            if metric.timestamp >= cutoff
        ]
    
    def get_execution_history(
        self,
        limit: int = 10
    ) -> List[Dict]:
        """
        دریافت تاریخچه اجرا
        
        Args:
            limit: حداکثر تعداد
        
        Returns:
            لیست اجراها
        """
        return self.execution_history[-limit:]


# ============================================================================
# Example Pipeline Functions
# ============================================================================

def extract_from_database(data: Any, context: Dict) -> pd.DataFrame:
    """Extract از database"""
    # TODO: پیاده‌سازی extract از database
    logger.info("Extracting from database")
    return pd.DataFrame()


def transform_normalize(data: pd.DataFrame, context: Dict) -> pd.DataFrame:
    """Transform: Normalize"""
    logger.info("Normalizing data")
    # TODO: پیاده‌سازی normalization
    return data


def load_to_feature_store(data: pd.DataFrame, context: Dict) -> bool:
    """Load به Feature Store"""
    logger.info("Loading to feature store")
    # TODO: پیاده‌سازی load
    return True

