"""
Treatment Coordination Engine
موتور هماهنگی درمان‌های مختلف
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from loguru import logger

from .models import TreatmentType, TreatmentParams, TreatmentPlan, TreatmentStatus


class CoordinationStrategy(Enum):
    """استراتژی هماهنگی"""
    SEQUENTIAL = "sequential"  # به ترتیب
    PARALLEL = "parallel"  # همزمان
    OPTIMIZED = "optimized"  # بهینه شده


@dataclass
class TreatmentInteraction:
    """تعامل بین درمان‌ها"""
    treatment1: TreatmentType
    treatment2: TreatmentType
    interaction_type: str  # "synergistic", "antagonistic", "neutral"
    strength: float  # 0-1


class TreatmentCoordinator:
    """هماهنگ‌کننده درمان‌ها"""
    
    def __init__(self):
        """مقداردهی اولیه"""
        self.active_plans: Dict[str, TreatmentPlan] = {}
        
        # ماتریس تعامل درمان‌ها
        self.interaction_matrix = self._build_interaction_matrix()
    
    def _build_interaction_matrix(self) -> Dict[Tuple[TreatmentType, TreatmentType], TreatmentInteraction]:
        """ساخت ماتریس تعامل درمان‌ها"""
        interactions = {}
        
        # تحریک عصبی + دارورسانی: synergistic
        interactions[(TreatmentType.STIMULATION, TreatmentType.DRUG_DELIVERY)] = TreatmentInteraction(
            treatment1=TreatmentType.STIMULATION,
            treatment2=TreatmentType.DRUG_DELIVERY,
            interaction_type="synergistic",
            strength=0.7
        )
        
        # سایر تعامل‌ها...
        
        return interactions
    
    def coordinate_treatments(
        self,
        patient_id: str,
        treatments: List[Dict],
        prediction_data: Optional[Dict] = None
    ) -> TreatmentPlan:
        """
        هماهنگی درمان‌ها
        
        Args:
            patient_id: شناسه بیمار
            treatments: لیست درمان‌های درخواستی
            prediction_data: داده‌های پیش‌بینی (اختیاری)
        
        Returns:
            برنامه درمان هماهنگ شده
        """
        # تبدیل به TreatmentParams
        treatment_params = []
        for t in treatments:
            treatment_params.append(
                TreatmentParams(
                    treatment_type=TreatmentType(t["treatment_type"]),
                    params=t["params"],
                    priority=t.get("priority", 0)
                )
            )
        
        # انتخاب استراتژی
        strategy = self._select_strategy(treatment_params, prediction_data)
        
        # بهینه‌سازی پارامترها
        optimized_params = self._optimize_parameters(treatment_params, prediction_data)
        
        # ایجاد برنامه
        plan = TreatmentPlan(
            patient_id=patient_id,
            treatments=optimized_params,
            strategy=strategy,
            start_time=datetime.now(),
            duration_hours=24,  # پیش‌فرض 24 ساعت
            status=TreatmentStatus.ACTIVE
        )
        
        # ذخیره
        self.active_plans[patient_id] = plan
        
        logger.info(f"Created treatment plan for patient {patient_id} with {len(optimized_params)} treatments")
        
        return plan
    
    def _select_strategy(
        self,
        treatments: List[TreatmentParams],
        prediction_data: Optional[Dict]
    ) -> CoordinationStrategy:
        """انتخاب استراتژی هماهنگی"""
        if len(treatments) == 1:
            return CoordinationStrategy.SEQUENTIAL
        
        # بررسی تعامل‌ها
        has_synergistic = False
        for i, t1 in enumerate(treatments):
            for t2 in treatments[i+1:]:
                key = (t1.treatment_type, t2.treatment_type)
                if key in self.interaction_matrix:
                    interaction = self.interaction_matrix[key]
                    if interaction.interaction_type == "synergistic":
                        has_synergistic = True
        
        if has_synergistic:
            return CoordinationStrategy.OPTIMIZED
        
        # اگر پیش‌بینی نشان دهد حمله قریب‌الوقوع است، از parallel استفاده می‌کنیم
        if prediction_data:
            risk_score = prediction_data.get("risk_score", 0)
            if risk_score > 0.7:
                return CoordinationStrategy.PARALLEL
        
        return CoordinationStrategy.SEQUENTIAL
    
    def _optimize_parameters(
        self,
        treatments: List[TreatmentParams],
        prediction_data: Optional[Dict]
    ) -> List[TreatmentParams]:
        """بهینه‌سازی پارامترهای درمان"""
        optimized = []
        
        for treatment in treatments:
            params = treatment.params.copy()
            
            # بررسی تعامل با سایر درمان‌ها
            for other_treatment in treatments:
                if other_treatment.treatment_type == treatment.treatment_type:
                    continue
                
                key = (treatment.treatment_type, other_treatment.treatment_type)
                if key in self.interaction_matrix:
                    interaction = self.interaction_matrix[key]
                    
                    if interaction.interaction_type == "synergistic":
                        # افزایش اثر با کاهش دوز
                        for param_key in params:
                            if param_key in ["intensity", "dose"]:
                                params[param_key] *= (1 - interaction.strength * 0.2)
                    
                    elif interaction.interaction_type == "antagonistic":
                        # افزایش دوز برای جبران
                        for param_key in params:
                            if param_key in ["intensity", "dose"]:
                                params[param_key] *= (1 + interaction.strength * 0.1)
            
            # تنظیم بر اساس پیش‌بینی
            if prediction_data:
                risk_score = prediction_data.get("risk_score", 0)
                attack_severity = prediction_data.get("attack_severity", 0)
                
                # افزایش شدت در صورت خطر بالا
                if risk_score > 0.7:
                    for param_key in params:
                        if param_key in ["intensity", "dose"]:
                            params[param_key] *= (1 + risk_score * 0.3)
            
            optimized.append(
                TreatmentParams(
                    treatment_type=treatment.treatment_type,
                    params=params,
                    priority=treatment.priority
                )
            )
        
        return optimized
    
    def get_current_plan(self, patient_id: str) -> Optional[TreatmentPlan]:
        """دریافت برنامه فعلی بیمار"""
        return self.active_plans.get(patient_id)
    
    def update_plan(self, patient_id: str, new_plan: TreatmentPlan):
        """به‌روزرسانی برنامه"""
        self.active_plans[patient_id] = new_plan
    
    def stop_plan(self, patient_id: str):
        """توقف برنامه"""
        if patient_id in self.active_plans:
            plan = self.active_plans[patient_id]
            plan.status = TreatmentStatus.STOPPED
            plan.end_time = datetime.now()

