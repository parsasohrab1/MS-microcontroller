"""
Auto Scaling Manager
مدیریت Auto-scaling برای Backend Services
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger
import asyncio
import httpx
import docker
from docker.errors import DockerException


class ScalingMetric(str, Enum):
    """متریک‌های scaling"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    REQUEST_RATE = "request_rate"
    RESPONSE_TIME = "response_time"
    QUEUE_LENGTH = "queue_length"


@dataclass
class ScalingPolicy:
    """سیاست scaling"""
    service_name: str
    min_instances: int
    max_instances: int
    target_cpu: float = 70.0  # درصد
    target_memory: float = 80.0  # درصد
    target_request_rate: float = 1000.0  # requests/second
    scale_up_threshold: float = 0.8  # 80% of target
    scale_down_threshold: float = 0.3  # 30% of target
    scale_up_cooldown: int = 60  # seconds
    scale_down_cooldown: int = 300  # seconds


@dataclass
class ServiceMetrics:
    """متریک‌های سرویس"""
    service_name: str
    cpu_usage: float
    memory_usage: float
    request_rate: float
    response_time_ms: float
    active_instances: int
    timestamp: datetime


class AutoScalingManager:
    """مدیریت Auto-scaling"""
    
    def __init__(self, docker_client: Optional[docker.DockerClient] = None):
        """
        مقداردهی اولیه
        
        Args:
            docker_client: Docker client (اختیاری)
        """
        self.docker_client = docker_client or docker.from_env()
        self.scaling_policies: Dict[str, ScalingPolicy] = {}
        self.service_metrics: Dict[str, List[ServiceMetrics]] = {}
        self.last_scale_time: Dict[str, datetime] = {}
        self.monitoring_active = False
    
    def register_service(self, policy: ScalingPolicy):
        """
        ثبت سرویس برای auto-scaling
        
        Args:
            policy: سیاست scaling
        """
        self.scaling_policies[policy.service_name] = policy
        self.service_metrics[policy.service_name] = []
        self.last_scale_time[policy.service_name] = datetime.now()
        
        logger.info(f"Registered service {policy.service_name} for auto-scaling")
    
    async def collect_metrics(self, service_name: str) -> Optional[ServiceMetrics]:
        """
        جمع‌آوری متریک‌های سرویس
        
        Args:
            service_name: نام سرویس
        
        Returns:
            متریک‌های سرویس
        """
        try:
            # دریافت متریک‌ها از Docker
            containers = self.docker_client.containers.list(
                filters={"name": service_name}
            )
            
            if not containers:
                return None
            
            total_cpu = 0.0
            total_memory = 0.0
            total_memory_limit = 0.0
            total_requests = 0.0
            total_response_time = 0.0
            
            for container in containers:
                stats = container.stats(stream=False)
                
                # محاسبه CPU usage
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                           stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                              stats['precpu_stats']['system_cpu_usage']
                
                if system_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * 100.0
                    total_cpu += cpu_percent
                
                # محاسبه Memory usage
                memory_usage = stats['memory_stats']['usage']
                memory_limit = stats['memory_stats']['limit']
                total_memory += memory_usage
                total_memory_limit += memory_limit
            
            # میانگین
            instance_count = len(containers)
            avg_cpu = total_cpu / instance_count if instance_count > 0 else 0
            avg_memory = (total_memory / total_memory_limit * 100) if total_memory_limit > 0 else 0
            
            # دریافت request rate از metrics endpoint
            request_rate = await self._get_request_rate(service_name)
            response_time = await self._get_response_time(service_name)
            
            metrics = ServiceMetrics(
                service_name=service_name,
                cpu_usage=avg_cpu,
                memory_usage=avg_memory,
                request_rate=request_rate,
                response_time_ms=response_time,
                active_instances=instance_count,
                timestamp=datetime.now()
            )
            
            # ذخیره متریک‌ها (حفظ آخرین 100)
            if service_name not in self.service_metrics:
                self.service_metrics[service_name] = []
            
            self.service_metrics[service_name].append(metrics)
            if len(self.service_metrics[service_name]) > 100:
                self.service_metrics[service_name] = self.service_metrics[service_name][-100:]
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error collecting metrics for {service_name}: {e}")
            return None
    
    async def _get_request_rate(self, service_name: str) -> float:
        """دریافت request rate از metrics endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://{service_name}:8000/metrics",
                    timeout=2.0
                )
                if response.status_code == 200:
                    # Parse Prometheus metrics
                    # TODO: Parse actual metrics
                    return 0.0
        except:
            pass
        return 0.0
    
    async def _get_response_time(self, service_name: str) -> float:
        """دریافت response time"""
        try:
            async with httpx.AsyncClient() as client:
                start = datetime.now()
                response = await client.get(
                    f"http://{service_name}:8000/health",
                    timeout=2.0
                )
                end = datetime.now()
                if response.status_code == 200:
                    return (end - start).total_seconds() * 1000
        except:
            pass
        return 0.0
    
    async def evaluate_scaling(self, service_name: str) -> Optional[int]:
        """
        ارزیابی نیاز به scaling
        
        Args:
            service_name: نام سرویس
        
        Returns:
            تعداد instances جدید (یا None اگر نیازی نیست)
        """
        if service_name not in self.scaling_policies:
            return None
        
        policy = self.scaling_policies[service_name]
        metrics = await self.collect_metrics(service_name)
        
        if not metrics:
            return None
        
        current_instances = metrics.active_instances
        
        # بررسی cooldown
        last_scale = self.last_scale_time.get(service_name, datetime.now() - timedelta(hours=1))
        elapsed = (datetime.now() - last_scale).total_seconds()
        
        # ارزیابی scale up
        should_scale_up = False
        if (
            metrics.cpu_usage > policy.target_cpu * policy.scale_up_threshold or
            metrics.memory_usage > policy.target_memory * policy.scale_up_threshold or
            metrics.request_rate > policy.target_request_rate * policy.scale_up_threshold
        ):
            if current_instances < policy.max_instances and elapsed > policy.scale_up_cooldown:
                should_scale_up = True
        
        # ارزیابی scale down
        should_scale_down = False
        if (
            metrics.cpu_usage < policy.target_cpu * policy.scale_down_threshold and
            metrics.memory_usage < policy.target_memory * policy.scale_down_threshold and
            metrics.request_rate < policy.target_request_rate * policy.scale_down_threshold
        ):
            if current_instances > policy.min_instances and elapsed > policy.scale_down_cooldown:
                should_scale_down = True
        
        # تصمیم‌گیری
        if should_scale_up:
            new_instances = min(current_instances + 1, policy.max_instances)
            logger.info(f"Scaling up {service_name}: {current_instances} -> {new_instances}")
            return new_instances
        
        if should_scale_down:
            new_instances = max(current_instances - 1, policy.min_instances)
            logger.info(f"Scaling down {service_name}: {current_instances} -> {new_instances}")
            return new_instances
        
        return None
    
    async def scale_service(self, service_name: str, target_instances: int) -> bool:
        """
        Scale کردن سرویس
        
        Args:
            service_name: نام سرویس
            target_instances: تعداد instances مورد نظر
        
        Returns:
            True در صورت موفقیت
        """
        try:
            policy = self.scaling_policies[service_name]
            
            # محدود کردن به min/max
            target_instances = max(policy.min_instances, 
                                 min(target_instances, policy.max_instances))
            
            current_containers = self.docker_client.containers.list(
                filters={"name": service_name}
            )
            current_count = len(current_containers)
            
            if target_instances > current_count:
                # Scale up
                instances_to_add = target_instances - current_count
                await self._scale_up(service_name, instances_to_add)
            
            elif target_instances < current_count:
                # Scale down
                instances_to_remove = current_count - target_instances
                await self._scale_down(service_name, instances_to_remove)
            
            self.last_scale_time[service_name] = datetime.now()
            return True
        
        except Exception as e:
            logger.error(f"Error scaling service {service_name}: {e}")
            return False
    
    async def _scale_up(self, service_name: str, count: int):
        """افزایش تعداد instances"""
        # استفاده از docker-compose scale
        # یا Kubernetes scale
        # TODO: پیاده‌سازی واقعی
        logger.info(f"Scaling up {service_name} by {count} instances")
    
    async def _scale_down(self, service_name: str, count: int):
        """کاهش تعداد instances"""
        # TODO: پیاده‌سازی واقعی
        logger.info(f"Scaling down {service_name} by {count} instances")
    
    async def start_monitoring(self, interval: int = 30):
        """
        شروع monitoring و auto-scaling
        
        Args:
            interval: فاصله بررسی (seconds)
        """
        self.monitoring_active = True
        
        while self.monitoring_active:
            for service_name in self.scaling_policies.keys():
                try:
                    target_instances = await self.evaluate_scaling(service_name)
                    if target_instances is not None:
                        await self.scale_service(service_name, target_instances)
                except Exception as e:
                    logger.error(f"Error in monitoring loop for {service_name}: {e}")
            
            await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """توقف monitoring"""
        self.monitoring_active = False

