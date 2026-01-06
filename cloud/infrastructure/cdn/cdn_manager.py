"""
CDN Manager
مدیریت CDN برای static content
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
import httpx
import hashlib
import os
from pathlib import Path


@dataclass
class CDNConfig:
    """تنظیمات CDN"""
    provider: str  # "cloudflare", "aws_cloudfront", "custom"
    endpoint: str
    api_key: Optional[str] = None
    zone_id: Optional[str] = None
    cache_ttl: int = 3600  # seconds
    enable_compression: bool = True
    enable_minification: bool = True


@dataclass
class CDNAsset:
    """Asset در CDN"""
    path: str
    url: str
    content_type: str
    size: int
    uploaded_at: datetime
    cache_key: str


class CDNManager:
    """مدیریت CDN"""
    
    def __init__(self, config: CDNConfig):
        """
        مقداردهی اولیه
        
        Args:
            config: تنظیمات CDN
        """
        self.config = config
        self.uploaded_assets: Dict[str, CDNAsset] = {}
    
    async def upload_static_file(
        self,
        file_path: str,
        cdn_path: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """
        آپلود فایل static به CDN
        
        Args:
            file_path: مسیر فایل محلی
            cdn_path: مسیر در CDN (اختیاری)
            content_type: نوع محتوا (اختیاری)
        
        Returns:
            URL فایل در CDN
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            # تعیین content type
            if not content_type:
                content_type = self._guess_content_type(file_path)
            
            # خواندن فایل
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # فشرده‌سازی (در صورت نیاز)
            if self.config.enable_compression:
                file_content = self._compress_content(file_content, content_type)
            
            # Minification (برای JS/CSS)
            if self.config.enable_minification:
                file_content = self._minify_content(file_content, content_type)
            
            # تعیین مسیر CDN
            if not cdn_path:
                cdn_path = os.path.basename(file_path)
            
            # آپلود به CDN
            cdn_url = await self._upload_to_cdn(cdn_path, file_content, content_type)
            
            if cdn_url:
                # ذخیره metadata
                asset = CDNAsset(
                    path=cdn_path,
                    url=cdn_url,
                    content_type=content_type,
                    size=len(file_content),
                    uploaded_at=datetime.now(),
                    cache_key=self._generate_cache_key(file_content)
                )
                self.uploaded_assets[cdn_path] = asset
                
                logger.info(f"Uploaded {file_path} to CDN: {cdn_url}")
            
            return cdn_url
        
        except Exception as e:
            logger.error(f"Error uploading file to CDN: {e}")
            return None
    
    async def upload_directory(
        self,
        directory_path: str,
        base_cdn_path: str = "",
        extensions: Optional[List[str]] = None
    ) -> List[str]:
        """
        آپلود دایرکتوری به CDN
        
        Args:
            directory_path: مسیر دایرکتوری
            base_cdn_path: مسیر پایه در CDN
            extensions: لیست پسوندهای مجاز (None = همه)
        
        Returns:
            لیست URL های آپلود شده
        """
        uploaded_urls = []
        
        if not extensions:
            extensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2']
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file)
                
                if ext.lower() in extensions:
                    # محاسبه مسیر نسبی
                    rel_path = os.path.relpath(file_path, directory_path)
                    cdn_path = os.path.join(base_cdn_path, rel_path).replace('\\', '/')
                    
                    url = await self.upload_static_file(file_path, cdn_path)
                    if url:
                        uploaded_urls.append(url)
        
        return uploaded_urls
    
    async def invalidate_cache(self, paths: List[str]) -> bool:
        """
        پاک کردن cache CDN
        
        Args:
            paths: لیست مسیرها برای پاک کردن
        
        Returns:
            True در صورت موفقیت
        """
        try:
            if self.config.provider == "cloudflare":
                return await self._cloudflare_purge_cache(paths)
            elif self.config.provider == "aws_cloudfront":
                return await self._cloudfront_invalidate(paths)
            else:
                logger.warning(f"Cache invalidation not supported for {self.config.provider}")
                return False
        
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False
    
    async def _upload_to_cdn(
        self,
        path: str,
        content: bytes,
        content_type: str
    ) -> Optional[str]:
        """آپلود به CDN (implementation specific)"""
        if self.config.provider == "cloudflare":
            return await self._upload_to_cloudflare(path, content, content_type)
        elif self.config.provider == "aws_cloudfront":
            return await self._upload_to_s3(path, content, content_type)
        else:
            # Custom CDN
            return await self._upload_to_custom(path, content, content_type)
    
    async def _upload_to_cloudflare(
        self,
        path: str,
        content: bytes,
        content_type: str
    ) -> Optional[str]:
        """آپلود به Cloudflare"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.config.endpoint}/{path}",
                    content=content,
                    headers={
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": content_type
                    }
                )
                
                if response.status_code == 200:
                    return f"{self.config.endpoint}/{path}"
        
        except Exception as e:
            logger.error(f"Error uploading to Cloudflare: {e}")
        
        return None
    
    async def _upload_to_s3(
        self,
        path: str,
        content: bytes,
        content_type: str
    ) -> Optional[str]:
        """آپلود به S3/CloudFront"""
        # TODO: استفاده از boto3
        return None
    
    async def _upload_to_custom(
        self,
        path: str,
        content: bytes,
        content_type: str
    ) -> Optional[str]:
        """آپلود به CDN سفارشی"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.config.endpoint}/upload",
                    json={
                        "path": path,
                        "content": content.hex(),  # یا base64
                        "content_type": content_type
                    },
                    headers={"Authorization": f"Bearer {self.config.api_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("url")
        
        except Exception as e:
            logger.error(f"Error uploading to custom CDN: {e}")
        
        return None
    
    async def _cloudflare_purge_cache(self, paths: List[str]) -> bool:
        """پاک کردن cache Cloudflare"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.cloudflare.com/client/v4/zones/{self.config.zone_id}/purge_cache",
                    json={"files": paths},
                    headers={
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                return response.status_code == 200
        
        except Exception as e:
            logger.error(f"Error purging Cloudflare cache: {e}")
            return False
    
    async def _cloudfront_invalidate(self, paths: List[str]) -> bool:
        """Invalidate CloudFront cache"""
        # TODO: استفاده از boto3
        return False
    
    def _guess_content_type(self, file_path: str) -> str:
        """تشخیص نوع محتوا"""
        ext = os.path.splitext(file_path)[1].lower()
        
        content_types = {
            '.js': 'application/javascript',
            '.css': 'text/css',
            '.html': 'text/html',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
            '.json': 'application/json'
        }
        
        return content_types.get(ext, 'application/octet-stream')
    
    def _compress_content(self, content: bytes, content_type: str) -> bytes:
        """فشرده‌سازی محتوا"""
        # فقط برای text-based content
        if content_type.startswith('text/') or content_type in ['application/javascript', 'application/json']:
            import gzip
            return gzip.compress(content)
        return content
    
    def _minify_content(self, content: bytes, content_type: str) -> bytes:
        """Minification محتوا"""
        # TODO: استفاده از minifiers (jsmin, cssmin)
        return content
    
    def _generate_cache_key(self, content: bytes) -> str:
        """تولید cache key"""
        return hashlib.md5(content).hexdigest()

