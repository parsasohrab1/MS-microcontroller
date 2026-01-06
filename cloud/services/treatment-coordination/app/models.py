"""
Models for Treatment Coordination
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


class TreatmentType(str, Enum):
    """نوع درمان"""
    STIMULATION = "stimulation"  # تحریک عصبی
    DRUG_DELIVERY = "drug_delivery"  # دارورسانی
    PHYSIOTHERAPY = "physiotherapy"  # فیزیوتراپی
    COGNITIVE_THERAPY = "cognitive_therapy"  # درمان شناختی


class TreatmentStatus(str, Enum):
    """وضعیت درمان"""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"


@dataclass
class TreatmentParams:
    """پارامترهای درمان"""
    treatment_type: TreatmentType
    params: Dict[str, float]  # پارامترهای خاص درمان
    priority: int = 0  # 0=normal, 1=high, 2=critical
    start_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None


@dataclass
class TreatmentPlan:
    """برنامه درمان"""
    patient_id: str
    treatments: list[TreatmentParams]
    strategy: str  # "sequential", "parallel", "optimized"
    start_time: datetime
    duration_hours: int
    status: TreatmentStatus = TreatmentStatus.PENDING
    end_time: Optional[datetime] = None
    notes: Optional[str] = None
    
    def dict(self):
        """تبدیل به dict برای JSON"""
        return {
            "patient_id": self.patient_id,
            "treatments": [
                {
                    "treatment_type": t.treatment_type.value,
                    "params": t.params,
                    "priority": t.priority
                }
                for t in self.treatments
            ],
            "strategy": self.strategy,
            "start_time": self.start_time.isoformat(),
            "duration_hours": self.duration_hours,
            "status": self.status.value,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "notes": self.notes
        }

