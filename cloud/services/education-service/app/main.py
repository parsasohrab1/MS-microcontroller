"""
Education Service
سیستم آموزش بیمار
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime
from pathlib import Path
import json

app = FastAPI(
    title="Education Service",
    description="سیستم آموزش و منابع اطلاعاتی برای بیماران",
    version="1.0.0"
)


class ContentType(str, Enum):
    """نوع محتوا"""
    VIDEO = "video"
    ARTICLE = "article"
    FAQ = "faq"
    GUIDE = "guide"
    INFographic = "infographic"


class Language(str, Enum):
    """زبان"""
    PERSIAN = "fa"
    ENGLISH = "en"
    ARABIC = "ar"


class EducationContent(BaseModel):
    """محتوی آموزشی"""
    id: str
    title: str
    description: str
    content_type: ContentType
    language: Language
    content_url: str
    thumbnail_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


class FAQ(BaseModel):
    """سوالات متداول"""
    id: str
    question: str
    answer: str
    category: str
    language: Language
    helpful_count: int = 0
    not_helpful_count: int = 0


# Database simulation (در production از پایگاه داده واقعی استفاده شود)
education_content_db: Dict[str, EducationContent] = {}
faq_db: Dict[str, FAQ] = {}


@app.get("/content")
async def get_content(
    content_type: Optional[ContentType] = None,
    language: Language = Language.PERSIAN,
    tags: Optional[List[str]] = None
) -> List[EducationContent]:
    """دریافت محتوی آموزشی"""
    results = list(education_content_db.values())
    
    # فیلتر بر اساس نوع
    if content_type:
        results = [c for c in results if c.content_type == content_type]
    
    # فیلتر بر اساس زبان
    results = [c for c in results if c.language == language]
    
    # فیلتر بر اساس تگ‌ها
    if tags:
        results = [c for c in results if any(tag in c.tags for tag in tags)]
    
    return results


@app.get("/content/{content_id}")
async def get_content_by_id(content_id: str) -> EducationContent:
    """دریافت محتوی خاص"""
    if content_id not in education_content_db:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return education_content_db[content_id]


@app.get("/faq")
async def get_faq(
    category: Optional[str] = None,
    language: Language = Language.PERSIAN,
    search_query: Optional[str] = None
) -> List[FAQ]:
    """دریافت FAQ"""
    results = list(faq_db.values())
    
    # فیلتر بر اساس دسته
    if category:
        results = [f for f in results if f.category == category]
    
    # فیلتر بر اساس زبان
    results = [f for f in results if f.language == language]
    
    # جستجو
    if search_query:
        query_lower = search_query.lower()
        results = [
            f for f in results
            if query_lower in f.question.lower() or query_lower in f.answer.lower()
        ]
    
    return results


@app.post("/faq/{faq_id}/feedback")
async def submit_faq_feedback(faq_id: str, helpful: bool):
    """ثبت بازخورد FAQ"""
    if faq_id not in faq_db:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    faq = faq_db[faq_id]
    if helpful:
        faq.helpful_count += 1
    else:
        faq.not_helpful_count += 1
    
    return {"status": "success"}


@app.get("/categories")
async def get_categories(language: Language = Language.PERSIAN) -> List[str]:
    """دریافت دسته‌بندی‌ها"""
    categories = set()
    
    for content in education_content_db.values():
        if content.language == language:
            categories.update(content.tags)
    
    return sorted(list(categories))


@app.get("/guide/system-usage")
async def get_system_usage_guide(language: Language = Language.PERSIAN) -> Dict:
    """راهنمای استفاده از سیستم"""
    guides = {
        Language.PERSIAN: {
            "title": "راهنمای استفاده از سیستم",
            "sections": [
                {
                    "title": "شروع کار",
                    "content": "برای شروع، دستگاه را روشن کنید و با اپلیکیشن موبایل جفت کنید."
                },
                {
                    "title": "نظارت بر داده‌ها",
                    "content": "در داشبورد می‌توانید داده‌های real-time را مشاهده کنید."
                },
                {
                    "title": "هشدارها",
                    "content": "در صورت دریافت هشدار، اقدامات پیشنهادی را دنبال کنید."
                }
            ]
        },
        Language.ENGLISH: {
            "title": "System Usage Guide",
            "sections": [
                {
                    "title": "Getting Started",
                    "content": "To begin, turn on the device and pair it with the mobile app."
                }
            ]
        }
    }
    
    return guides.get(language, guides[Language.PERSIAN])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)

