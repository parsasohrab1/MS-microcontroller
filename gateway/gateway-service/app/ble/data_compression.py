"""
Data Compression for BLE
فشرده‌سازی داده‌ها برای بهینه‌سازی bandwidth
"""

import zlib
import gzip
import lzma
import json
import base64
from typing import Any, Dict, Optional
from enum import Enum
from loguru import logger


class CompressionAlgorithm(Enum):
    """الگوریتم‌های فشرده‌سازی"""
    NONE = "none"
    ZLIB = "zlib"
    GZIP = "gzip"
    LZMA = "lzma"


class DataCompressor:
    """فشرده‌سازی داده‌ها"""
    
    def __init__(self, algorithm: CompressionAlgorithm = CompressionAlgorithm.ZLIB):
        """
        مقداردهی اولیه
        
        Args:
            algorithm: الگوریتم فشرده‌سازی
        """
        self.algorithm = algorithm
    
    def compress(
        self,
        data: Any,
        serialize: bool = True
    ) -> bytes:
        """
        فشرده‌سازی داده
        
        Args:
            data: داده (dict, list, str, bytes)
            serialize: آیا باید JSON serialize شود
        
        Returns:
            داده فشرده شده (bytes)
        """
        try:
            # تبدیل به bytes
            if serialize and isinstance(data, (dict, list)):
                data_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
            elif isinstance(data, str):
                data_bytes = data.encode('utf-8')
            elif isinstance(data, bytes):
                data_bytes = data
            else:
                data_bytes = str(data).encode('utf-8')
            
            # فشرده‌سازی
            if self.algorithm == CompressionAlgorithm.NONE:
                return data_bytes
            elif self.algorithm == CompressionAlgorithm.ZLIB:
                return zlib.compress(data_bytes, level=6)
            elif self.algorithm == CompressionAlgorithm.GZIP:
                return gzip.compress(data_bytes, compresslevel=6)
            elif self.algorithm == CompressionAlgorithm.LZMA:
                return lzma.compress(data_bytes, preset=6)
            else:
                return data_bytes
        
        except Exception as e:
            logger.error(f"Compression error: {e}")
            # در صورت خطا، داده بدون فشرده‌سازی برمی‌گردد
            if isinstance(data, bytes):
                return data
            return str(data).encode('utf-8')
    
    def decompress(
        self,
        compressed_data: bytes,
        deserialize: bool = True
    ) -> Any:
        """
        از حالت فشرده خارج کردن
        
        Args:
            compressed_data: داده فشرده شده
            deserialize: آیا باید JSON deserialize شود
        
        Returns:
            داده اصلی
        """
        try:
            # از حالت فشرده خارج کردن
            if self.algorithm == CompressionAlgorithm.NONE:
                data_bytes = compressed_data
            elif self.algorithm == CompressionAlgorithm.ZLIB:
                data_bytes = zlib.decompress(compressed_data)
            elif self.algorithm == CompressionAlgorithm.GZIP:
                data_bytes = gzip.decompress(compressed_data)
            elif self.algorithm == CompressionAlgorithm.LZMA:
                data_bytes = lzma.decompress(compressed_data)
            else:
                data_bytes = compressed_data
            
            # Deserialize
            if deserialize:
                try:
                    return json.loads(data_bytes.decode('utf-8'))
                except json.JSONDecodeError:
                    return data_bytes.decode('utf-8')
            
            return data_bytes
        
        except Exception as e:
            logger.error(f"Decompression error: {e}")
            return compressed_data
    
    def compress_base64(
        self,
        data: Any,
        serialize: bool = True
    ) -> str:
        """
        فشرده‌سازی و تبدیل به base64 (برای انتقال در text)
        
        Args:
            data: داده
            serialize: آیا باید JSON serialize شود
        
        Returns:
            رشته base64
        """
        compressed = self.compress(data, serialize=serialize)
        return base64.b64encode(compressed).decode('utf-8')
    
    def decompress_base64(
        self,
        base64_data: str,
        deserialize: bool = True
    ) -> Any:
        """
        از base64 خارج کردن و از حالت فشرده خارج کردن
        
        Args:
            base64_data: رشته base64
            deserialize: آیا باید JSON deserialize شود
        
        Returns:
            داده اصلی
        """
        compressed_data = base64.b64decode(base64_data)
        return self.decompress(compressed_data, deserialize=deserialize)
    
    def get_compression_ratio(self, original: bytes, compressed: bytes) -> float:
        """
        محاسبه نسبت فشرده‌سازی
        
        Args:
            original: داده اصلی
            compressed: داده فشرده شده
        
        Returns:
            نسبت (0-1)
        """
        if len(original) == 0:
            return 0.0
        return len(compressed) / len(original)


# Singleton instances
_compressors: Dict[CompressionAlgorithm, DataCompressor] = {}


def get_compressor(algorithm: CompressionAlgorithm = CompressionAlgorithm.ZLIB) -> DataCompressor:
    """دریافت instance Compressor"""
    if algorithm not in _compressors:
        _compressors[algorithm] = DataCompressor(algorithm)
    return _compressors[algorithm]

