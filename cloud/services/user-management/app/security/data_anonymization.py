"""
Data Anonymization
پیاده‌سازی Data Anonymization برای استفاده از داده‌ها در پژوهش
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger
import hashlib
import uuid
import random


# ============================================================================
# Anonymization Methods
# ============================================================================

class AnonymizationMethod:
    """روش‌های anonymization"""
    
    @staticmethod
    def hash_value(value: str, salt: Optional[str] = None) -> str:
        """
        Hash کردن مقدار
        
        Args:
            value: مقدار برای hash
            salt: Salt (اختیاری)
        
        Returns:
            Hash شده
        """
        if salt:
            value = f"{value}{salt}"
        
        return hashlib.sha256(value.encode()).hexdigest()[:16]
    
    @staticmethod
    def pseudonymize(value: str, mapping: Dict[str, str]) -> str:
        """
        Pseudonymization
        
        Args:
            value: مقدار اصلی
            mapping: Mapping برای pseudonymization
        
        Returns:
            Pseudonymized value
        """
        if value not in mapping:
            mapping[value] = str(uuid.uuid4())
        
        return mapping[value]
    
    @staticmethod
    def generalize_date(date: datetime, level: str = "month") -> str:
        """
        Generalization تاریخ
        
        Args:
            date: تاریخ
            level: سطح (year, month, quarter)
        
        Returns:
            تاریخ generalized شده
        """
        if level == "year":
            return date.strftime("%Y")
        elif level == "month":
            return date.strftime("%Y-%m")
        elif level == "quarter":
            quarter = (date.month - 1) // 3 + 1
            return f"{date.year}-Q{quarter}"
        
        return date.isoformat()
    
    @staticmethod
    def generalize_age(age: int, range_size: int = 10) -> str:
        """
        Generalization سن
        
        Args:
            age: سن
            range_size: اندازه بازه
        
        Returns:
            بازه سنی
        """
        lower = (age // range_size) * range_size
        upper = lower + range_size
        return f"{lower}-{upper}"
    
    @staticmethod
    def generalize_location(location: str, level: str = "city") -> str:
        """
        Generalization مکان
        
        Args:
            location: مکان
            level: سطح (country, state, city)
        
        Returns:
            مکان generalized شده
        """
        # TODO: پیاده‌سازی واقعی
        # در حال حاضر placeholder
        parts = location.split(",")
        if level == "country" and len(parts) > 0:
            return parts[-1].strip()
        elif level == "state" and len(parts) > 1:
            return parts[-2].strip()
        elif level == "city" and len(parts) > 2:
            return parts[-3].strip()
        
        return location
    
    @staticmethod
    def add_noise(value: float, noise_level: float = 0.1) -> float:
        """
        اضافه کردن noise
        
        Args:
            value: مقدار
            noise_level: سطح noise (درصد)
        
        Returns:
            مقدار با noise
        """
        noise = random.uniform(-noise_level, noise_level) * value
        return value + noise
    
    @staticmethod
    def k_anonymize(data: List[Dict], k: int = 5) -> List[Dict]:
        """
        K-anonymity
        
        Args:
            data: داده
            k: مقدار k
        
        Returns:
            داده anonymized
        """
        # TODO: پیاده‌سازی واقعی k-anonymity
        # در حال حاضر placeholder
        return data


# ============================================================================
# Data Anonymizer
# ============================================================================

class DataAnonymizer:
    """Anonymizer برای داده‌ها"""
    
    def __init__(self):
        """مقداردهی اولیه"""
        self.pseudonym_mapping: Dict[str, str] = {}
        self.salt: str = str(uuid.uuid4())
    
    def anonymize_patient_data(
        self,
        patient_data: Dict,
        anonymization_level: str = "medium"
    ) -> Dict:
        """
        Anonymize کردن داده‌های patient
        
        Args:
            patient_data: داده‌های patient
            anonymization_level: سطح anonymization (low, medium, high)
        
        Returns:
            داده anonymized
        """
        anonymized = patient_data.copy()
        
        # حذف شناسه‌های مستقیم
        if anonymization_level in ["medium", "high"]:
            anonymized.pop("patient_id", None)
            anonymized.pop("email", None)
            anonymized.pop("phone", None)
            anonymized.pop("address", None)
        
        # Pseudonymization
        if "name" in anonymized:
            anonymized["name"] = AnonymizationMethod.pseudonymize(
                anonymized["name"],
                self.pseudonym_mapping
            )
        
        # Generalization تاریخ
        if "birth_date" in anonymized:
            birth_date = datetime.fromisoformat(anonymized["birth_date"])
            if anonymization_level == "high":
                anonymized["birth_date"] = AnonymizationMethod.generalize_date(
                    birth_date, "year"
                )
            elif anonymization_level == "medium":
                anonymized["birth_date"] = AnonymizationMethod.generalize_date(
                    birth_date, "quarter"
                )
        
        # Generalization سن
        if "age" in anonymized:
            anonymized["age"] = AnonymizationMethod.generalize_age(
                anonymized["age"],
                range_size=10 if anonymization_level == "high" else 5
            )
        
        # Generalization مکان
        if "location" in anonymized:
            if anonymization_level == "high":
                anonymized["location"] = AnonymizationMethod.generalize_location(
                    anonymized["location"], "country"
                )
            elif anonymization_level == "medium":
                anonymized["location"] = AnonymizationMethod.generalize_location(
                    anonymized["location"], "state"
                )
        
        # اضافه کردن noise به داده‌های عددی
        if anonymization_level == "high":
            for key in ["weight", "height", "bmi"]:
                if key in anonymized and isinstance(anonymized[key], (int, float)):
                    anonymized[key] = AnonymizationMethod.add_noise(
                        anonymized[key],
                        noise_level=0.05
                    )
        
        return anonymized
    
    def anonymize_sensor_data(
        self,
        sensor_data: List[Dict],
        anonymization_level: str = "medium"
    ) -> List[Dict]:
        """
        Anonymize کردن داده‌های sensor
        
        Args:
            sensor_data: داده‌های sensor
            anonymization_level: سطح anonymization
        
        Returns:
            داده anonymized
        """
        anonymized = []
        
        for data_point in sensor_data:
            anon_point = data_point.copy()
            
            # حذف timestamp دقیق
            if "timestamp" in anon_point:
                timestamp = datetime.fromisoformat(anon_point["timestamp"])
                if anonymization_level == "high":
                    # Round به ساعت
                    anon_point["timestamp"] = timestamp.replace(
                        minute=0, second=0, microsecond=0
                    ).isoformat()
                elif anonymization_level == "medium":
                    # Round به 10 دقیقه
                    minutes = (timestamp.minute // 10) * 10
                    anon_point["timestamp"] = timestamp.replace(
                        minute=minutes, second=0, microsecond=0
                    ).isoformat()
            
            # اضافه کردن noise به داده‌های sensor
            if anonymization_level == "high":
                for key in ["value", "eeg_data", "biomarker_values"]:
                    if key in anon_point:
                        if isinstance(anon_point[key], list):
                            anon_point[key] = [
                                AnonymizationMethod.add_noise(v, 0.02)
                                for v in anon_point[key]
                            ]
                        elif isinstance(anon_point[key], (int, float)):
                            anon_point[key] = AnonymizationMethod.add_noise(
                                anon_point[key], 0.02
                            )
            
            anonymized.append(anon_point)
        
        return anonymized
    
    def anonymize_treatment_data(
        self,
        treatment_data: Dict,
        anonymization_level: str = "medium"
    ) -> Dict:
        """
        Anonymize کردن داده‌های treatment
        
        Args:
            treatment_data: داده‌های treatment
            anonymization_level: سطح anonymization
        
        Returns:
            داده anonymized
        """
        anonymized = treatment_data.copy()
        
        # حذف شناسه‌ها
        if anonymization_level in ["medium", "high"]:
            anonymized.pop("patient_id", None)
            anonymized.pop("doctor_id", None)
        
        # Generalization تاریخ
        if "start_date" in anonymized:
            start_date = datetime.fromisoformat(anonymized["start_date"])
            anonymized["start_date"] = AnonymizationMethod.generalize_date(
                start_date,
                "month" if anonymization_level == "high" else "quarter"
            )
        
        # Generalization دوز
        if "dosage" in anonymized and anonymization_level == "high":
            dosage = anonymized["dosage"]
            anonymized["dosage"] = f"{dosage // 10 * 10}-{dosage // 10 * 10 + 10}"
        
        return anonymized
    
    def check_k_anonymity(self, data: List[Dict], k: int = 5) -> bool:
        """
        بررسی k-anonymity
        
        Args:
            data: داده
            k: مقدار k
        
        Returns:
            True اگر k-anonymous است
        """
        # TODO: پیاده‌سازی واقعی
        # در حال حاضر placeholder
        return len(data) >= k


# Singleton instance
_data_anonymizer: Optional[DataAnonymizer] = None


def get_data_anonymizer() -> DataAnonymizer:
    """دریافت instance data anonymizer"""
    global _data_anonymizer
    if _data_anonymizer is None:
        _data_anonymizer = DataAnonymizer()
    return _data_anonymizer

