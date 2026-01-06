"""
Message Queue Client - RabbitMQ
کلاینت برای ارتباط با RabbitMQ
"""

import pika
import json
from typing import Callable, Optional, Dict, Any
from loguru import logger
import os
from functools import wraps
import time


class RabbitMQClient:
    """کلاینت RabbitMQ برای ارسال و دریافت پیام‌ها"""
    
    def __init__(self, connection_url: Optional[str] = None):
        """
        مقداردهی اولیه کلاینت
        
        Args:
            connection_url: URL اتصال RabbitMQ
                مثال: amqp://user:pass@localhost:5672/
        """
        self.connection_url = connection_url or os.getenv(
            "RABBITMQ_URL",
            "amqp://admin:admin@localhost:5672/"
        )
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self._connect()
    
    def _connect(self):
        """اتصال به RabbitMQ"""
        try:
            parameters = pika.URLParameters(self.connection_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def _ensure_connection(self):
        """اطمینان از اتصال"""
        if self.connection is None or self.connection.is_closed:
            self._connect()
    
    def declare_queue(self, queue_name: str, durable: bool = True):
        """
        تعریف صف
        
        Args:
            queue_name: نام صف
            durable: آیا صف باید پایدار باشد (survive restart)
        """
        self._ensure_connection()
        self.channel.queue_declare(queue=queue_name, durable=durable)
        logger.debug(f"Queue declared: {queue_name}")
    
    def declare_exchange(self, exchange_name: str, exchange_type: str = "topic"):
        """
        تعریف exchange
        
        Args:
            exchange_name: نام exchange
            exchange_type: نوع exchange (direct, topic, fanout, headers)
        """
        self._ensure_connection()
        self.channel.exchange_declare(
            exchange=exchange_name,
            exchange_type=exchange_type,
            durable=True
        )
        logger.debug(f"Exchange declared: {exchange_name} ({exchange_type})")
    
    def bind_queue(self, queue_name: str, exchange_name: str, routing_key: str):
        """
        اتصال صف به exchange
        
        Args:
            queue_name: نام صف
            exchange_name: نام exchange
            routing_key: کلید routing
        """
        self._ensure_connection()
        self.channel.queue_bind(
            exchange=exchange_name,
            queue=queue_name,
            routing_key=routing_key
        )
        logger.debug(f"Queue {queue_name} bound to {exchange_name} with key {routing_key}")
    
    def publish_message(
        self,
        queue_name: str,
        message: Dict[str, Any],
        exchange: str = "",
        routing_key: Optional[str] = None,
        persistent: bool = True
    ):
        """
        ارسال پیام به صف
        
        Args:
            queue_name: نام صف
            message: پیام (dict)
            exchange: نام exchange (خالی برای default)
            routing_key: کلید routing (اگر None باشد، از queue_name استفاده می‌شود)
            persistent: آیا پیام باید پایدار باشد
        """
        self._ensure_connection()
        
        # تعریف صف اگر وجود نداشته باشد
        self.declare_queue(queue_name, durable=persistent)
        
        # تبدیل پیام به JSON
        message_body = json.dumps(message).encode('utf-8')
        
        # تنظیمات پیام
        properties = pika.BasicProperties(
            delivery_mode=2 if persistent else 1,  # 2 = persistent
            timestamp=int(time.time())
        )
        
        routing = routing_key or queue_name
        
        # ارسال پیام
        self.channel.basic_publish(
            exchange=exchange,
            routing_key=routing,
            body=message_body,
            properties=properties
        )
        
        logger.debug(f"Message published to {queue_name}")
    
    def publish_to_exchange(
        self,
        exchange_name: str,
        routing_key: str,
        message: Dict[str, Any],
        persistent: bool = True
    ):
        """
        ارسال پیام به exchange
        
        Args:
            exchange_name: نام exchange
            routing_key: کلید routing
            message: پیام (dict)
            persistent: آیا پیام باید پایدار باشد
        """
        self._ensure_connection()
        
        # تعریف exchange
        self.declare_exchange(exchange_name, exchange_type="topic")
        
        # تبدیل پیام به JSON
        message_body = json.dumps(message).encode('utf-8')
        
        # تنظیمات پیام
        properties = pika.BasicProperties(
            delivery_mode=2 if persistent else 1,
            timestamp=int(time.time())
        )
        
        # ارسال پیام
        self.channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=message_body,
            properties=properties
        )
        
        logger.debug(f"Message published to exchange {exchange_name} with key {routing_key}")
    
    def consume_messages(
        self,
        queue_name: str,
        callback: Callable[[Dict[str, Any], Any], bool],
        auto_ack: bool = False,
        prefetch_count: int = 1
    ):
        """
        دریافت و پردازش پیام‌ها از صف
        
        Args:
            queue_name: نام صف
            callback: تابع callback برای پردازش پیام
                باید (message_dict, delivery_tag) را دریافت کند و True/False برگرداند
            auto_ack: آیا پیام به صورت خودکار acknowledge شود
            prefetch_count: تعداد پیام‌های پیش‌بارگذاری شده
        """
        self._ensure_connection()
        
        # تعریف صف
        self.declare_queue(queue_name, durable=True)
        
        # تنظیم prefetch
        self.channel.basic_qos(prefetch_count=prefetch_count)
        
        def on_message(ch, method, properties, body):
            """Handler برای دریافت پیام"""
            try:
                # تبدیل JSON به dict
                message = json.loads(body.decode('utf-8'))
                
                # اجرای callback
                success = callback(message, method.delivery_tag)
                
                # Acknowledge پیام
                if not auto_ack:
                    if success:
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    else:
                        # Reject و requeue
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode message: {e}")
                if not auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                if not auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        # شروع مصرف
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=on_message,
            auto_ack=auto_ack
        )
        
        logger.info(f"Started consuming from queue: {queue_name}")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            logger.info("Stopped consuming")
    
    def close(self):
        """بستن اتصال"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")


# Singleton instance
_rabbitmq_client: Optional[RabbitMQClient] = None


def get_rabbitmq_client() -> RabbitMQClient:
    """دریافت instance کلاینت RabbitMQ"""
    global _rabbitmq_client
    if _rabbitmq_client is None:
        _rabbitmq_client = RabbitMQClient()
    return _rabbitmq_client


# Decorator برای retry
def retry_on_connection_error(max_retries: int = 3, delay: float = 1.0):
    """Decorator برای retry در صورت خطای اتصال"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (pika.exceptions.AMQPConnectionError, pika.exceptions.AMQPChannelError) as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Connection error, retrying ({attempt + 1}/{max_retries}): {e}")
                        time.sleep(delay * (attempt + 1))
                    else:
                        logger.error(f"Max retries reached: {e}")
                        raise
        return wrapper
    return decorator

