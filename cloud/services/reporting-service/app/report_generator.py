"""
Report Generator Service
سیستم گزارش‌گیری خودکار
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import io


class ReportType(str, Enum):
    """نوع گزارش"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """فرمت گزارش"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


@dataclass
class ReportData:
    """داده‌های گزارش"""
    patient_id: str
    period_start: datetime
    period_end: datetime
    report_type: ReportType
    
    # آمار
    total_readings: int
    average_risk_score: float
    max_risk_score: float
    min_risk_score: float
    
    # هشدارها
    alert_count: int
    alerts: List[Dict]
    
    # حملات
    attack_count: int
    attacks: List[Dict]
    
    # درمان
    treatment_sessions: int
    treatment_effectiveness: float
    
    # مقایسه با دوره قبل
    previous_period_comparison: Optional[Dict] = None


class ReportGenerator:
    """تولیدکننده گزارش"""
    
    def __init__(self, output_dir: str = "reports"):
        """
        مقداردهی اولیه
        
        Args:
            output_dir: مسیر ذخیره گزارش‌ها
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # ثبت فونت فارسی (در صورت نیاز)
        try:
            pdfmetrics.registerFont(
                TTFont('Persian', 'fonts/Vazir-Regular.ttf')
            )
        except:
            pass  # اگر فونت موجود نبود، از فونت پیش‌فرض استفاده می‌شود
    
    def generate_report(
        self,
        report_data: ReportData,
        format: ReportFormat = ReportFormat.PDF
    ) -> str:
        """
        تولید گزارش
        
        Args:
            report_data: داده‌های گزارش
            format: فرمت خروجی
        
        Returns:
            مسیر فایل ایجاد شده
        """
        if format == ReportFormat.PDF:
            return self._generate_pdf(report_data)
        elif format == ReportFormat.EXCEL:
            return self._generate_excel(report_data)
        elif format == ReportFormat.CSV:
            return self._generate_csv(report_data)
        elif format == ReportFormat.JSON:
            return self._generate_json(report_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_pdf(self, report_data: ReportData) -> str:
        """تولید گزارش PDF"""
        filename = f"report_{report_data.patient_id}_{report_data.period_start.strftime('%Y%m%d')}.pdf"
        filepath = self.output_dir / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # عنوان
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=1  # center
        )
        story.append(Paragraph("گزارش بیمار", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # اطلاعات دوره
        info_data = [
            ['شناسه بیمار:', report_data.patient_id],
            ['دوره:', f"{report_data.period_start.strftime('%Y-%m-%d')} تا {report_data.period_end.strftime('%Y-%m-%d')}"],
            ['نوع گزارش:', report_data.report_type.value],
            ['تاریخ ایجاد:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ]
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # آمار کلی
        story.append(Paragraph("آمار کلی", styles['Heading2']))
        stats_data = [
            ['متریک', 'مقدار'],
            ['تعداد خوانش‌ها', str(report_data.total_readings)],
            ['میانگین امتیاز خطر', f"{(report_data.average_risk_score * 100):.1f}%"],
            ['حداکثر امتیاز خطر', f"{(report_data.max_risk_score * 100):.1f}%"],
            ['حداقل امتیاز خطر', f"{(report_data.min_risk_score * 100):.1f}%"],
            ['تعداد هشدارها', str(report_data.alert_count)],
            ['تعداد حملات', str(report_data.attack_count)],
            ['جلسات درمان', str(report_data.treatment_sessions)],
            ['اثربخشی درمان', f"{(report_data.treatment_effectiveness * 100):.1f}%"],
        ]
        stats_table = Table(stats_data, colWidths=[3*inch, 3*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 0.3*inch))
        
        # مقایسه با دوره قبل
        if report_data.previous_period_comparison:
            story.append(Paragraph("مقایسه با دوره قبل", styles['Heading2']))
            comp_data = [
                ['متریک', 'دوره فعلی', 'دوره قبل', 'تغییر'],
                [
                    'میانگین امتیاز خطر',
                    f"{(report_data.average_risk_score * 100):.1f}%",
                    f"{(report_data.previous_period_comparison.get('average_risk_score', 0) * 100):.1f}%",
                    self._format_change(
                        report_data.average_risk_score,
                        report_data.previous_period_comparison.get('average_risk_score', 0)
                    )
                ],
                [
                    'تعداد حملات',
                    str(report_data.attack_count),
                    str(report_data.previous_period_comparison.get('attack_count', 0)),
                    self._format_change(
                        report_data.attack_count,
                        report_data.previous_period_comparison.get('attack_count', 0),
                        is_percentage=False
                    )
                ],
            ]
            comp_table = Table(comp_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
            comp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(comp_table)
        
        # ساخت PDF
        doc.build(story)
        
        return str(filepath)
    
    def _generate_excel(self, report_data: ReportData) -> str:
        """تولید گزارش Excel"""
        filename = f"report_{report_data.patient_id}_{report_data.period_start.strftime('%Y%m%d')}.xlsx"
        filepath = self.output_dir / filename
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Sheet 1: آمار کلی
            summary_data = {
                'متریک': [
                    'تعداد خوانش‌ها',
                    'میانگین امتیاز خطر',
                    'حداکثر امتیاز خطر',
                    'حداقل امتیاز خطر',
                    'تعداد هشدارها',
                    'تعداد حملات',
                    'جلسات درمان',
                    'اثربخشی درمان'
                ],
                'مقدار': [
                    report_data.total_readings,
                    f"{(report_data.average_risk_score * 100):.1f}%",
                    f"{(report_data.max_risk_score * 100):.1f}%",
                    f"{(report_data.min_risk_score * 100):.1f}%",
                    report_data.alert_count,
                    report_data.attack_count,
                    report_data.treatment_sessions,
                    f"{(report_data.treatment_effectiveness * 100):.1f}%"
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='آمار کلی', index=False)
            
            # Sheet 2: هشدارها
            if report_data.alerts:
                df_alerts = pd.DataFrame(report_data.alerts)
                df_alerts.to_excel(writer, sheet_name='هشدارها', index=False)
            
            # Sheet 3: حملات
            if report_data.attacks:
                df_attacks = pd.DataFrame(report_data.attacks)
                df_attacks.to_excel(writer, sheet_name='حملات', index=False)
        
        return str(filepath)
    
    def _generate_csv(self, report_data: ReportData) -> str:
        """تولید گزارش CSV"""
        filename = f"report_{report_data.patient_id}_{report_data.period_start.strftime('%Y%m%d')}.csv"
        filepath = self.output_dir / filename
        
        data = {
            'patient_id': [report_data.patient_id],
            'period_start': [report_data.period_start.isoformat()],
            'period_end': [report_data.period_end.isoformat()],
            'total_readings': [report_data.total_readings],
            'average_risk_score': [report_data.average_risk_score],
            'alert_count': [report_data.alert_count],
            'attack_count': [report_data.attack_count],
        }
        
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        return str(filepath)
    
    def _generate_json(self, report_data: ReportData) -> str:
        """تولید گزارش JSON"""
        filename = f"report_{report_data.patient_id}_{report_data.period_start.strftime('%Y%m%d')}.json"
        filepath = self.output_dir / filename
        
        data = {
            'patient_id': report_data.patient_id,
            'period_start': report_data.period_start.isoformat(),
            'period_end': report_data.period_end.isoformat(),
            'report_type': report_data.report_type.value,
            'total_readings': report_data.total_readings,
            'average_risk_score': report_data.average_risk_score,
            'max_risk_score': report_data.max_risk_score,
            'min_risk_score': report_data.min_risk_score,
            'alert_count': report_data.alert_count,
            'alerts': report_data.alerts,
            'attack_count': report_data.attack_count,
            'attacks': report_data.attacks,
            'treatment_sessions': report_data.treatment_sessions,
            'treatment_effectiveness': report_data.treatment_effectiveness,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def _format_change(self, current: float, previous: float, is_percentage: bool = True) -> str:
        """فرمت تغییر"""
        if previous == 0:
            return "N/A"
        
        change = current - previous
        change_percent = (change / previous) * 100 if previous != 0 else 0
        
        if is_percentage:
            sign = "+" if change_percent >= 0 else ""
            return f"{sign}{change_percent:.1f}%"
        else:
            sign = "+" if change >= 0 else ""
            return f"{sign}{change:.1f}"


# Singleton instance
_report_generator: Optional[ReportGenerator] = None


def get_report_generator() -> ReportGenerator:
    """دریافت instance Report Generator"""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator

