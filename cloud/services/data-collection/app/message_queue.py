"""
Message Queue Integration
"""

from typing import Dict, Any
import json
from loguru import logger
import sys
import os

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

try:
    from message_queue import RabbitMQClient
    
    # Initialize client
    rabbitmq_client = RabbitMQClient()
except ImportError:
    logger.warning("RabbitMQ client not available")
    rabbitmq_client = None


async def publish_to_queue(queue_name: str, message: Dict[str, Any]):
    """
    ارسال پیام به queue
    
    Args:
        queue_name: نام queue
        message: پیام
    """
    if not rabbitmq_client:
        logger.warning("RabbitMQ not available, skipping message publish")
        return
    
    try:
        await rabbitmq_client.publish(queue_name, json.dumps(message))
        logger.info(f"Published message to {queue_name}")
    except Exception as e:
        logger.error(f"Error publishing to queue: {e}")

