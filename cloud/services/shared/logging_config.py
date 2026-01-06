"""
Centralized Logging Configuration
پیکربندی Centralized Logging با ELK Stack
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
import socket
from loguru import logger
import sys


class ELKFormatter(logging.Formatter):
    """Formatter برای ELK Stack"""
    
    def __init__(self, service_name: str, environment: str = "production"):
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.hostname = socket.gethostname()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record برای ELK"""
        log_data = {
            "@timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": self.service_name,
            "environment": self.environment,
            "hostname": self.hostname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # اضافه کردن exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # اضافه کردن extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


def setup_logging(
    service_name: str,
    environment: str = "production",
    log_level: str = "INFO",
    elk_enabled: bool = True,
    elk_host: str = "logstash",
    elk_port: int = 5044
):
    """
    Setup centralized logging
    
    Args:
        service_name: نام سرویس
        environment: محیط (staging, production)
        log_level: سطح لاگ
        elk_enabled: فعال بودن ELK
        elk_host: آدرس Logstash
        elk_port: پورت Logstash
    """
    # Remove default handler
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # File handler
    logger.add(
        f"logs/{service_name}.log",
        rotation="100 MB",
        retention="30 days",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        compression="zip"
    )
    
    # ELK handler (TCP to Logstash)
    if elk_enabled:
        try:
            import socket
            
            class LogstashHandler(logging.Handler):
                def __init__(self, host, port):
                    super().__init__()
                    self.host = host
                    self.port = port
                    self.sock = None
                
                def emit(self, record):
                    try:
                        if not self.sock:
                            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            self.sock.connect((self.host, self.port))
                        
                        log_data = {
                            "@timestamp": datetime.utcnow().isoformat(),
                            "level": record.levelname,
                            "message": self.format(record),
                            "service": service_name,
                            "environment": environment,
                            "hostname": socket.gethostname(),
                        }
                        
                        self.sock.send((json.dumps(log_data) + "\n").encode())
                    except Exception as e:
                        print(f"Error sending log to Logstash: {e}")
            
            # Add Logstash handler
            logstash_handler = LogstashHandler(elk_host, elk_port)
            logstash_handler.setFormatter(ELKFormatter(service_name, environment))
            
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(logstash_handler)
            root_logger.setLevel(getattr(logging, log_level))
        
        except Exception as e:
            logger.warning(f"Failed to setup ELK logging: {e}")


def log_with_context(
    level: str,
    message: str,
    extra_fields: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """
    Log با context اضافی
    
    Args:
        level: سطح لاگ
        message: پیام
        extra_fields: فیلدهای اضافی
        **kwargs: فیلدهای اضافی دیگر
    """
    context = extra_fields or {}
    context.update(kwargs)
    
    logger.bind(**context).log(level.upper(), message)

