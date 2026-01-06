"""
Advanced Alert System
سیستم هشدار پیشرفته چندمرحله‌ای
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from loguru import logger


class AlertLevel(str, Enum):
    """سطح هشدار"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertRecipient(str, Enum):
    """گیرنده هشدار"""
    PATIENT = "patient"
    DOCTOR = "doctor"
    NURSE = "nurse"
    FAMILY = "family"
    EMERGENCY_CONTACT = "emergency_contact"


@dataclass
class AlertStage:
    """مرحله هشدار"""
    time_before_attack_hours: float  # ساعت قبل از حمله
    level: AlertLevel
    recipients: List[AlertRecipient]
    message_template: str
    actions: List[str] = field(default_factory=list)  # اقدامات پیشنهادی


@dataclass
class Alert:
    """هشدار"""
    alert_id: str
    patient_id: str
    stage: AlertStage
    message: str
    timestamp: datetime
    sent: bool = False
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class AdvancedAlertSystem:
    """سیستم هشدار پیشرفته"""
    
    def __init__(self):
        """مقداردهی اولیه"""
        self.alert_stages = self._create_default_stages()
        self.active_alerts: Dict[str, List[Alert]] = {}  # patient_id -> alerts
        self.alert_callbacks: Dict[str, Callable] = {}
    
    def _create_default_stages(self) -> List[AlertStage]:
        """ایجاد مراحل پیش‌فرض هشدار"""
        return [
            AlertStage(
                time_before_attack_hours=24.0,
                level=AlertLevel.INFO,
                recipients=[AlertRecipient.PATIENT, AlertRecipient.DOCTOR],
                message_template="هشدار اولیه: احتمال حمله در 24 ساعت آینده",
                actions=["مصرف داروهای پیشگیرانه", "استراحت", "نظارت بر علائم"]
            ),
            AlertStage(
                time_before_attack_hours=12.0,
                level=AlertLevel.WARNING,
                recipients=[AlertRecipient.PATIENT, AlertRecipient.DOCTOR, AlertRecipient.NURSE],
                message_template="هشدار: احتمال حمله در 12 ساعت آینده",
                actions=["تماس با پزشک", "آماده‌سازی داروها", "اجتناب از فعالیت‌های سنگین"]
            ),
            AlertStage(
                time_before_attack_hours=6.0,
                level=AlertLevel.WARNING,
                recipients=[AlertRecipient.PATIENT, AlertRecipient.DOCTOR, AlertRecipient.NURSE, AlertRecipient.FAMILY],
                message_template="هشدار فوری: احتمال حمله در 6 ساعت آینده",
                actions=["تماس فوری با پزشک", "شروع درمان پیشگیرانه", "آماده‌سازی برای مراجعه به بیمارستان"]
            ),
            AlertStage(
                time_before_attack_hours=1.0,
                level=AlertLevel.CRITICAL,
                recipients=[
                    AlertRecipient.PATIENT,
                    AlertRecipient.DOCTOR,
                    AlertRecipient.NURSE,
                    AlertRecipient.FAMILY,
                    AlertRecipient.EMERGENCY_CONTACT
                ],
                message_template="هشدار بحرانی: احتمال حمله در 1 ساعت آینده",
                actions=["شروع درمان فوری", "آماده‌سازی برای انتقال به بیمارستان", "تماس با اورژانس"]
            )
        ]
    
    def register_callback(self, recipient: AlertRecipient, callback: Callable):
        """ثبت callback برای ارسال هشدار"""
        self.alert_callbacks[recipient.value] = callback
    
    def process_prediction(
        self,
        patient_id: str,
        prediction_data: Dict,
        predicted_attack_time: Optional[datetime] = None
    ) -> List[Alert]:
        """
        پردازش پیش‌بینی و ایجاد هشدارها
        
        Args:
            patient_id: شناسه بیمار
            prediction_data: داده‌های پیش‌بینی
            predicted_attack_time: زمان پیش‌بینی شده حمله
        
        Returns:
            لیست هشدارهای ایجاد شده
        """
        if predicted_attack_time is None:
            # محاسبه زمان حمله بر اساس پیش‌بینی
            risk_score = prediction_data.get("risk_score", 0)
            if risk_score < 0.5:
                return []  # خطر پایین، هشداری لازم نیست
            
            # تخمین زمان حمله (مثلاً 24 ساعت برای risk_score=0.8)
            hours_until_attack = 24 * (1 - risk_score)
            predicted_attack_time = datetime.now() + timedelta(hours=hours_until_attack)
        
        alerts = []
        now = datetime.now()
        
        for stage in self.alert_stages:
            alert_time = predicted_attack_time - timedelta(hours=stage.time_before_attack_hours)
            
            # بررسی اینکه آیا زمان هشدار رسیده است
            if alert_time <= now:
                # بررسی اینکه آیا قبلاً ارسال شده
                if not self._is_alert_sent(patient_id, stage):
                    alert = self._create_alert(patient_id, stage, prediction_data, predicted_attack_time)
                    alerts.append(alert)
        
        # ذخیره هشدارها
        if patient_id not in self.active_alerts:
            self.active_alerts[patient_id] = []
        
        self.active_alerts[patient_id].extend(alerts)
        
        # ارسال هشدارها
        for alert in alerts:
            asyncio.create_task(self._send_alert(alert))
        
        return alerts
    
    def _create_alert(
        self,
        patient_id: str,
        stage: AlertStage,
        prediction_data: Dict,
        predicted_attack_time: datetime
    ) -> Alert:
        """ایجاد هشدار"""
        import uuid
        
        # ساخت پیام
        message = stage.message_template
        if "risk_score" in prediction_data:
            message += f" (امتیاز خطر: {prediction_data['risk_score']:.2f})"
        
        # اضافه کردن اقدامات
        if stage.actions:
            message += "\nاقدامات پیشنهادی:\n"
            for i, action in enumerate(stage.actions, 1):
                message += f"{i}. {action}\n"
        
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            patient_id=patient_id,
            stage=stage,
            message=message,
            timestamp=datetime.now()
        )
        
        return alert
    
    def _is_alert_sent(self, patient_id: str, stage: AlertStage) -> bool:
        """بررسی اینکه آیا هشدار قبلاً ارسال شده"""
        if patient_id not in self.active_alerts:
            return False
        
        for alert in self.active_alerts[patient_id]:
            if alert.stage.time_before_attack_hours == stage.time_before_attack_hours:
                return alert.sent
        
        return False
    
    async def _send_alert(self, alert: Alert):
        """ارسال هشدار به گیرندگان"""
        for recipient in alert.stage.recipients:
            callback = self.alert_callbacks.get(recipient.value)
            if callback:
                try:
                    await callback(alert, recipient)
                    logger.info(f"Alert sent to {recipient.value} for patient {alert.patient_id}")
                except Exception as e:
                    logger.error(f"Error sending alert to {recipient.value}: {e}")
            else:
                logger.warning(f"No callback registered for {recipient.value}")
        
        alert.sent = True
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """تأیید هشدار"""
        for patient_id, alerts in self.active_alerts.items():
            for alert in alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    alert.acknowledged_by = acknowledged_by
                    alert.acknowledged_at = datetime.now()
                    return True
        return False
    
    def get_patient_alerts(self, patient_id: str, active_only: bool = True) -> List[Alert]:
        """دریافت هشدارهای بیمار"""
        if patient_id not in self.active_alerts:
            return []
        
        alerts = self.active_alerts[patient_id]
        
        if active_only:
            # فقط هشدارهای ارسال نشده یا تأیید نشده
            alerts = [a for a in alerts if not a.acknowledged]
        
        return alerts

