"""
Bandwidth Optimization for BLE
بهینه‌سازی bandwidth برای انتقال داده
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from loguru import logger

from .data_compression import DataCompressor, CompressionAlgorithm


@dataclass
class DataPacket:
    """بسته داده"""
    data: Any
    priority: int = 0  # 0 = normal, 1 = high, 2 = critical
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3


class BandwidthOptimizer:
    """بهینه‌سازی bandwidth"""
    
    def __init__(
        self,
        max_queue_size: int = 100,
        batch_size: int = 10,
        batch_timeout: float = 1.0,  # 1 second
        compression_enabled: bool = True,
        compression_algorithm: CompressionAlgorithm = CompressionAlgorithm.ZLIB,
        priority_queue: bool = True
    ):
        """
        مقداردهی اولیه
        
        Args:
            max_queue_size: حداکثر اندازه صف
            batch_size: اندازه batch برای ارسال
            batch_timeout: زمان انتظار برای تشکیل batch (ثانیه)
            compression_enabled: فعال بودن فشرده‌سازی
            compression_algorithm: الگوریتم فشرده‌سازی
            priority_queue: استفاده از صف اولویت‌دار
        """
        self.max_queue_size = max_queue_size
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.compression_enabled = compression_enabled
        self.compression_algorithm = compression_algorithm
        self.priority_queue = priority_queue
        
        self.compressor = DataCompressor(compression_algorithm) if compression_enabled else None
        
        # صف‌های داده
        if priority_queue:
            self._critical_queue: deque = deque()
            self._high_queue: deque = deque()
            self._normal_queue: deque = deque()
        else:
            self._queue: deque = deque()
        
        self._batch_lock = asyncio.Lock()
        self._batch_task: Optional[asyncio.Task] = None
        
        # آمار
        self._stats = {
            "total_sent": 0,
            "total_compressed": 0,
            "total_bytes_saved": 0,
            "total_batches": 0
        }
    
    def enqueue(
        self,
        data: Any,
        priority: int = 0,
        max_retries: int = 3
    ) -> bool:
        """
        اضافه کردن داده به صف
        
        Args:
            data: داده
            priority: اولویت (0=normal, 1=high, 2=critical)
            max_retries: حداکثر تلاش برای ارسال
        
        Returns:
            True در صورت موفقیت
        """
        if self.priority_queue:
            packet = DataPacket(data=data, priority=priority, max_retries=max_retries)
            
            if priority >= 2:
                if len(self._critical_queue) >= self.max_queue_size:
                    logger.warning("Critical queue full, dropping oldest packet")
                    self._critical_queue.popleft()
                self._critical_queue.append(packet)
            elif priority >= 1:
                if len(self._high_queue) >= self.max_queue_size:
                    logger.warning("High queue full, dropping oldest packet")
                    self._high_queue.popleft()
                self._high_queue.append(packet)
            else:
                if len(self._normal_queue) >= self.max_queue_size:
                    logger.warning("Normal queue full, dropping oldest packet")
                    self._normal_queue.popleft()
                self._normal_queue.append(packet)
        else:
            if len(self._queue) >= self.max_queue_size:
                logger.warning("Queue full, dropping oldest packet")
                self._queue.popleft()
            
            packet = DataPacket(data=data, priority=priority, max_retries=max_retries)
            self._queue.append(packet)
        
        # شروع batch task اگر وجود نداشته باشد
        if self._batch_task is None or self._batch_task.done():
            self._batch_task = asyncio.create_task(self._batch_processor())
        
        return True
    
    async def _batch_processor(self):
        """پردازش batch"""
        while True:
            try:
                # جمع‌آوری بسته‌ها
                batch = await self._collect_batch()
                
                if batch:
                    # پردازش batch
                    await self._process_batch(batch)
                
                # بررسی اینکه آیا داده‌ای در صف هست
                if self.priority_queue:
                    has_data = (
                        len(self._critical_queue) > 0 or
                        len(self._high_queue) > 0 or
                        len(self._normal_queue) > 0
                    )
                else:
                    has_data = len(self._queue) > 0
                
                if not has_data:
                    break
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
                await asyncio.sleep(0.1)
    
    async def _collect_batch(self) -> List[DataPacket]:
        """جمع‌آوری بسته‌ها برای batch"""
        batch = []
        start_time = datetime.now()
        
        while len(batch) < self.batch_size:
            # بررسی timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed >= self.batch_timeout and len(batch) > 0:
                break
            
            # دریافت بسته از صف
            packet = self._dequeue_packet()
            if packet:
                batch.append(packet)
            else:
                # اگر صف خالی است، منتظر بمان
                await asyncio.sleep(0.1)
        
        return batch
    
    def _dequeue_packet(self) -> Optional[DataPacket]:
        """خارج کردن بسته از صف (با اولویت)"""
        if self.priority_queue:
            # اول critical
            if len(self._critical_queue) > 0:
                return self._critical_queue.popleft()
            # سپس high
            if len(self._high_queue) > 0:
                return self._high_queue.popleft()
            # در نهایت normal
            if len(self._normal_queue) > 0:
                return self._normal_queue.popleft()
        else:
            if len(self._queue) > 0:
                return self._queue.popleft()
        
        return None
    
    async def _process_batch(self, batch: List[DataPacket]):
        """پردازش batch"""
        # ترکیب داده‌ها
        batch_data = [packet.data for packet in batch]
        
        # فشرده‌سازی
        if self.compression_enabled and self.compressor:
            original_size = len(str(batch_data).encode('utf-8'))
            compressed_data = self.compressor.compress(batch_data)
            compressed_size = len(compressed_data)
            
            bytes_saved = original_size - compressed_size
            self._stats["total_compressed"] += 1
            self._stats["total_bytes_saved"] += bytes_saved
            
            logger.debug(
                f"Compressed batch: {original_size} -> {compressed_size} bytes "
                f"(saved {bytes_saved} bytes, {bytes_saved/original_size*100:.1f}%)"
            )
            
            data_to_send = compressed_data
        else:
            data_to_send = batch_data
        
        # ارسال (باید توسط caller پیاده‌سازی شود)
        # await self._send_batch(data_to_send)
        
        self._stats["total_sent"] += len(batch)
        self._stats["total_batches"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """دریافت آمار"""
        queue_sizes = {}
        if self.priority_queue:
            queue_sizes = {
                "critical": len(self._critical_queue),
                "high": len(self._high_queue),
                "normal": len(self._normal_queue)
            }
        else:
            queue_sizes = {"total": len(self._queue)}
        
        return {
            **self._stats,
            "queue_sizes": queue_sizes,
            "compression_enabled": self.compression_enabled
        }
    
    def clear_queue(self):
        """پاک کردن صف"""
        if self.priority_queue:
            self._critical_queue.clear()
            self._high_queue.clear()
            self._normal_queue.clear()
        else:
            self._queue.clear()


# Singleton instance
_bandwidth_optimizer: Optional[BandwidthOptimizer] = None


def get_bandwidth_optimizer() -> BandwidthOptimizer:
    """دریافت instance Bandwidth Optimizer"""
    global _bandwidth_optimizer
    if _bandwidth_optimizer is None:
        _bandwidth_optimizer = BandwidthOptimizer()
    return _bandwidth_optimizer

