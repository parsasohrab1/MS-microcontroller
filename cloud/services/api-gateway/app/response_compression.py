"""
Response Compression
فشرده‌سازی پاسخ‌های API
"""

from typing import Optional
from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
import gzip
import brotli
from loguru import logger


class CompressionMiddleware(BaseHTTPMiddleware):
    """Middleware برای فشرده‌سازی پاسخ"""
    
    def __init__(self, app, minimum_size: int = 500, compress_level: int = 6):
        """
        مقداردهی اولیه
        
        Args:
            app: FastAPI app
            minimum_size: حداقل اندازه برای فشرده‌سازی (bytes)
            compress_level: سطح فشرده‌سازی (1-9)
        """
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compress_level = compress_level
    
    async def dispatch(self, request: Request, call_next):
        """
        پردازش request و فشرده‌سازی پاسخ
        
        Args:
            request: FastAPI request
            call_next: تابع بعدی در middleware chain
        """
        # دریافت پاسخ
        response = await call_next(request)
        
        # بررسی نیاز به فشرده‌سازی
        if not self._should_compress(request, response):
            return response
        
        # بررسی Accept-Encoding
        accept_encoding = request.headers.get("Accept-Encoding", "")
        
        # انتخاب الگوریتم فشرده‌سازی
        if "br" in accept_encoding:
            return await self._compress_brotli(response)
        elif "gzip" in accept_encoding:
            return await self._compress_gzip(response)
        else:
            return response
    
    def _should_compress(self, request: Request, response: Response) -> bool:
        """
        بررسی اینکه آیا باید فشرده‌سازی انجام شود
        
        Args:
            request: FastAPI request
            response: FastAPI response
        
        Returns:
            True اگر باید فشرده‌سازی شود
        """
        # بررسی content type
        content_type = response.headers.get("Content-Type", "")
        
        # فشرده‌سازی فقط برای text-based content
        compressible_types = [
            "application/json",
            "application/javascript",
            "text/html",
            "text/css",
            "text/plain",
            "text/xml",
            "application/xml"
        ]
        
        if not any(ct in content_type for ct in compressible_types):
            return False
        
        # بررسی اندازه
        content_length = response.headers.get("Content-Length")
        if content_length:
            if int(content_length) < self.minimum_size:
                return False
        
        # بررسی اینکه قبلاً فشرده نشده باشد
        if response.headers.get("Content-Encoding"):
            return False
        
        return True
    
    async def _compress_gzip(self, response: Response) -> Response:
        """فشرده‌سازی با GZIP"""
        try:
            # خواندن محتوای پاسخ
            body = b""
            if hasattr(response, "body"):
                body = response.body
            elif hasattr(response, "body_iterator"):
                async for chunk in response.body_iterator:
                    body += chunk
            
            # فشرده‌سازی
            compressed = gzip.compress(body, compresslevel=self.compress_level)
            
            # بررسی اینکه آیا فشرده‌سازی مفید بوده
            if len(compressed) >= len(body):
                return response  # فشرده‌سازی مفید نبوده
            
            # ایجاد پاسخ جدید
            compressed_response = Response(
                content=compressed,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
            # اضافه کردن header
            compressed_response.headers["Content-Encoding"] = "gzip"
            compressed_response.headers["Content-Length"] = str(len(compressed))
            compressed_response.headers["Vary"] = "Accept-Encoding"
            
            # حذف Content-Length اصلی
            if "Content-Length" in compressed_response.headers:
                original_length = compressed_response.headers["Content-Length"]
                compressed_response.headers["X-Original-Content-Length"] = original_length
            
            return compressed_response
        
        except Exception as e:
            logger.error(f"Error compressing response with gzip: {e}")
            return response
    
    async def _compress_brotli(self, response: Response) -> Response:
        """فشرده‌سازی با Brotli"""
        try:
            # خواندن محتوای پاسخ
            body = b""
            if hasattr(response, "body"):
                body = response.body
            elif hasattr(response, "body_iterator"):
                async for chunk in response.body_iterator:
                    body += chunk
            
            # فشرده‌سازی
            compressed = brotli.compress(body, quality=self.compress_level)
            
            # بررسی اینکه آیا فشرده‌سازی مفید بوده
            if len(compressed) >= len(body):
                return response
            
            # ایجاد پاسخ جدید
            compressed_response = Response(
                content=compressed,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
            # اضافه کردن header
            compressed_response.headers["Content-Encoding"] = "br"
            compressed_response.headers["Content-Length"] = str(len(compressed))
            compressed_response.headers["Vary"] = "Accept-Encoding"
            
            return compressed_response
        
        except Exception as e:
            logger.error(f"Error compressing response with brotli: {e}")
            return response


def get_compression_ratio(original_size: int, compressed_size: int) -> float:
    """
    محاسبه نسبت فشرده‌سازی
    
    Args:
        original_size: اندازه اصلی
        compressed_size: اندازه فشرده
    
    Returns:
        نسبت فشرده‌سازی (0-1)
    """
    if original_size == 0:
        return 0.0
    return 1.0 - (compressed_size / original_size)

