"""
Adaptive Learning System
سیستم یادگیری تطبیقی برای شخصی‌سازی درمان
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from pathlib import Path
from collections import deque
import pickle


@dataclass
class PatientResponse:
    """پاسخ بیمار به درمان"""
    timestamp: datetime
    treatment_params: Dict[str, float]  # پارامترهای درمان اعمال شده
    patient_outcome: float  # نتیجه (0-1): 0 = بدتر، 1 = بهتر
    side_effects: float  # عوارض جانبی (0-1)
    patient_feedback: Optional[float] = None  # بازخورد بیمار (0-1)


@dataclass
class PatientProfile:
    """پروفایل بیمار برای یادگیری تطبیقی"""
    patient_id: str
    baseline_features: Dict[str, float]  # ویژگی‌های پایه
    treatment_history: List[PatientResponse] = field(default_factory=list)
    optimal_params: Optional[Dict[str, float]] = None
    learning_rate: float = 0.1
    exploration_rate: float = 0.2
    last_updated: Optional[datetime] = None


class AdaptiveLearningSystem:
    """سیستم یادگیری تطبیقی"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        مقداردهی اولیه
        
        Args:
            storage_path: مسیر ذخیره‌سازی پروفایل‌های بیماران
        """
        self.storage_path = storage_path or "patient_profiles"
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
        
        self.patient_profiles: Dict[str, PatientProfile] = {}
        self.load_all_profiles()
    
    def get_or_create_profile(self, patient_id: str) -> PatientProfile:
        """دریافت یا ایجاد پروفایل بیمار"""
        if patient_id not in self.patient_profiles:
            self.patient_profiles[patient_id] = PatientProfile(
                patient_id=patient_id,
                baseline_features={}
            )
        return self.patient_profiles[patient_id]
    
    def record_response(
        self,
        patient_id: str,
        treatment_params: Dict[str, float],
        patient_outcome: float,
        side_effects: float = 0.0,
        patient_feedback: Optional[float] = None
    ):
        """
        ثبت پاسخ بیمار به درمان
        
        Args:
            patient_id: شناسه بیمار
            treatment_params: پارامترهای درمان اعمال شده
            patient_outcome: نتیجه (0-1)
            side_effects: عوارض جانبی (0-1)
            patient_feedback: بازخورد بیمار (0-1)
        """
        profile = self.get_or_create_profile(patient_id)
        
        response = PatientResponse(
            timestamp=datetime.now(),
            treatment_params=treatment_params.copy(),
            patient_outcome=patient_outcome,
            side_effects=side_effects,
            patient_feedback=patient_feedback
        )
        
        profile.treatment_history.append(response)
        
        # محدود کردن تاریخچه (حفظ آخرین 1000 پاسخ)
        if len(profile.treatment_history) > 1000:
            profile.treatment_history = profile.treatment_history[-1000:]
        
        # به‌روزرسانی پارامترهای بهینه
        self._update_optimal_params(profile)
        
        profile.last_updated = datetime.now()
        
        # ذخیره
        self.save_profile(patient_id)
    
    def _update_optimal_params(self, profile: PatientProfile):
        """به‌روزرسانی پارامترهای بهینه بر اساس تاریخچه"""
        if len(profile.treatment_history) < 5:
            return  # نیاز به حداقل 5 پاسخ
        
        # محاسبه امتیاز ترکیبی (outcome - side_effects)
        scores = []
        params_list = []
        
        for response in profile.treatment_history[-50:]:  # آخرین 50 پاسخ
            score = response.patient_outcome - (response.side_effects * 0.5)
            if response.patient_feedback is not None:
                score = (score + response.patient_feedback) / 2
            
            scores.append(score)
            params_list.append(response.treatment_params)
        
        # پیدا کردن بهترین پارامترها
        best_idx = np.argmax(scores)
        best_params = params_list[best_idx]
        
        # Smoothing با پارامترهای قبلی
        if profile.optimal_params is None:
            profile.optimal_params = best_params.copy()
        else:
            for key in best_params:
                if key in profile.optimal_params:
                    # Weighted average
                    profile.optimal_params[key] = (
                        (1 - profile.learning_rate) * profile.optimal_params[key] +
                        profile.learning_rate * best_params[key]
                    )
                else:
                    profile.optimal_params[key] = best_params[key]
    
    def suggest_treatment_params(
        self,
        patient_id: str,
        base_params: Dict[str, float]
    ) -> Dict[str, float]:
        """
        پیشنهاد پارامترهای درمان
        
        Args:
            patient_id: شناسه بیمار
            base_params: پارامترهای پایه (از مدل عمومی)
        
        Returns:
            پارامترهای پیشنهادی (شخصی‌سازی شده)
        """
        profile = self.get_or_create_profile(patient_id)
        
        if profile.optimal_params is None or len(profile.treatment_history) < 3:
            # اگر تاریخچه کافی نیست، از پارامترهای پایه استفاده می‌کنیم
            return base_params.copy()
        
        # ترکیب پارامترهای بهینه با پارامترهای پایه
        suggested_params = {}
        
        for key in base_params:
            if key in profile.optimal_params:
                # Weighted combination
                weight = 0.7 if len(profile.treatment_history) > 10 else 0.5
                suggested_params[key] = (
                    weight * profile.optimal_params[key] +
                    (1 - weight) * base_params[key]
                )
            else:
                suggested_params[key] = base_params[key]
        
        # Exploration: اضافه کردن noise برای کشف بهتر
        if np.random.random() < profile.exploration_rate:
            for key in suggested_params:
                noise = np.random.normal(0, 0.05)  # 5% noise
                suggested_params[key] = np.clip(
                    suggested_params[key] + noise,
                    0.0, 1.0
                )
        
        return suggested_params
    
    def get_patient_insights(self, patient_id: str) -> Dict[str, any]:
        """دریافت بینش‌های بیمار"""
        if patient_id not in self.patient_profiles:
            return {}
        
        profile = self.patient_profiles[patient_id]
        
        if len(profile.treatment_history) == 0:
            return {
                "patient_id": patient_id,
                "total_responses": 0,
                "message": "No treatment history available"
            }
        
        # محاسبه آمار
        outcomes = [r.patient_outcome for r in profile.treatment_history]
        side_effects = [r.side_effects for r in profile.treatment_history]
        
        return {
            "patient_id": patient_id,
            "total_responses": len(profile.treatment_history),
            "average_outcome": np.mean(outcomes),
            "average_side_effects": np.mean(side_effects),
            "optimal_params": profile.optimal_params,
            "last_updated": profile.last_updated.isoformat() if profile.last_updated else None,
            "improvement_trend": self._calculate_trend(outcomes)
        }
    
    def _calculate_trend(self, values: List[float], window: int = 10) -> str:
        """محاسبه روند بهبود"""
        if len(values) < window:
            return "insufficient_data"
        
        recent = np.mean(values[-window:])
        previous = np.mean(values[-window*2:-window])
        
        if recent > previous + 0.1:
            return "improving"
        elif recent < previous - 0.1:
            return "declining"
        else:
            return "stable"
    
    def save_profile(self, patient_id: str):
        """ذخیره پروفایل بیمار"""
        if patient_id not in self.patient_profiles:
            return
        
        profile = self.patient_profiles[patient_id]
        file_path = Path(self.storage_path) / f"{patient_id}.pkl"
        
        with open(file_path, 'wb') as f:
            pickle.dump(profile, f)
    
    def load_profile(self, patient_id: str) -> bool:
        """بارگذاری پروفایل بیمار"""
        file_path = Path(self.storage_path) / f"{patient_id}.pkl"
        
        if not file_path.exists():
            return False
        
        with open(file_path, 'rb') as f:
            profile = pickle.load(f)
            self.patient_profiles[patient_id] = profile
        
        return True
    
    def load_all_profiles(self):
        """بارگذاری تمام پروفایل‌ها"""
        profile_dir = Path(self.storage_path)
        
        if not profile_dir.exists():
            return
        
        for file_path in profile_dir.glob("*.pkl"):
            patient_id = file_path.stem
            self.load_profile(patient_id)

