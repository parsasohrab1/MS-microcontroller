"""
Database Sharding
مدیریت Database Sharding برای مقیاس‌پذیری
"""

from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from loguru import logger
import hashlib
import json


class ShardingStrategy:
    """استراتژی sharding"""
    RANGE = "range"
    HASH = "hash"
    DIRECTORY = "directory"


class DatabaseShardManager:
    """مدیریت Database Shards"""
    
    def __init__(
        self,
        shard_configs: List[Dict[str, str]],
        sharding_key: str = "patient_id",
        strategy: str = ShardingStrategy.HASH
    ):
        """
        مقداردهی اولیه
        
        Args:
            shard_configs: لیست تنظیمات shards
            sharding_key: کلید sharding
            strategy: استراتژی sharding
        """
        self.shard_configs = shard_configs
        self.sharding_key = sharding_key
        self.strategy = strategy
        
        # ایجاد engines برای هر shard
        self.shard_engines = []
        self.shard_sessions = []
        
        for config in shard_configs:
            engine = create_engine(
                config['url'],
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True
            )
            self.shard_engines.append(engine)
            self.shard_sessions.append(sessionmaker(bind=engine))
        
        logger.info(f"Initialized {len(shard_configs)} database shards")
    
    def get_shard_index(self, sharding_value: Any) -> int:
        """
        تعیین shard برای مقدار مشخص
        
        Args:
            sharding_value: مقدار کلید sharding
        
        Returns:
            index shard
        """
        if self.strategy == ShardingStrategy.HASH:
            # استفاده از hash
            hash_value = int(hashlib.md5(str(sharding_value).encode()).hexdigest(), 16)
            return hash_value % len(self.shard_engines)
        
        elif self.strategy == ShardingStrategy.RANGE:
            # Range-based sharding
            # فرض: sharding_value یک عدد است
            if isinstance(sharding_value, (int, float)):
                shard_size = 1000000  # 1M records per shard
                return int(sharding_value) // shard_size % len(self.shard_engines)
            else:
                # Fallback به hash
                hash_value = int(hashlib.md5(str(sharding_value).encode()).hexdigest(), 16)
                return hash_value % len(self.shard_engines)
        
        elif self.strategy == ShardingStrategy.DIRECTORY:
            # Directory-based (مثلاً بر اساس patient_id prefix)
            if isinstance(sharding_value, str) and len(sharding_value) > 0:
                # استفاده از اولین کاراکتر
                char_value = ord(sharding_value[0].lower())
                return char_value % len(self.shard_engines)
            else:
                return 0
        
        return 0
    
    def get_shard_session(self, sharding_value: Any) -> Session:
        """
        دریافت session برای shard مشخص
        
        Args:
            sharding_value: مقدار کلید sharding
        
        Returns:
            Session
        """
        shard_index = self.get_shard_index(sharding_value)
        return self.shard_sessions[shard_index]()
    
    @contextmanager
    def shard_session(self, sharding_value: Any):
        """
        Context manager برای shard session
        
        Usage:
            with shard_manager.shard_session(patient_id) as session:
                result = session.query(Model).filter_by(patient_id=patient_id).all()
        """
        session = self.get_shard_session(sharding_value)
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Shard session error: {e}")
            raise
        finally:
            session.close()
    
    def query_all_shards(self, query_func) -> List[Any]:
        """
        اجرای query روی همه shards
        
        Args:
            query_func: تابع query که session را دریافت می‌کند
        
        Returns:
            لیست نتایج از همه shards
        """
        all_results = []
        
        for i, session_factory in enumerate(self.shard_sessions):
            try:
                session = session_factory()
                results = query_func(session)
                all_results.extend(results)
                session.close()
            except Exception as e:
                logger.error(f"Error querying shard {i}: {e}")
        
        return all_results
    
    def get_shard_stats(self) -> List[Dict]:
        """
        دریافت آمار shards
        
        Returns:
            لیست آمار shards
        """
        stats = []
        
        for i, engine in enumerate(self.shard_engines):
            try:
                with engine.connect() as conn:
                    # تعداد records
                    count_query = text("SELECT COUNT(*) FROM sensor_data")
                    result = conn.execute(count_query)
                    record_count = result.scalar() or 0
                    
                    # اندازه دیتابیس
                    size_query = text("""
                        SELECT pg_database_size(current_database())
                    """)
                    result = conn.execute(size_query)
                    db_size = result.scalar() or 0
                
                stats.append({
                    "shard_index": i,
                    "record_count": record_count,
                    "database_size_bytes": db_size,
                    "database_size_mb": db_size / (1024 * 1024)
                })
            
            except Exception as e:
                stats.append({
                    "shard_index": i,
                    "error": str(e)
                })
        
        return stats
    
    def rebalance_shards(self) -> bool:
        """
        Rebalance کردن shards
        
        Returns:
            True در صورت موفقیت
        """
        # TODO: پیاده‌سازی rebalancing
        # 1. بررسی توزیع داده
        # 2. انتقال داده از shards پر به shards خالی
        logger.info("Rebalancing shards...")
        return True
    
    def migrate_data(
        self,
        from_shard: int,
        to_shard: int,
        filter_condition: Optional[str] = None
    ) -> int:
        """
        انتقال داده بین shards
        
        Args:
            from_shard: shard مبدأ
            to_shard: shard مقصد
            filter_condition: شرط فیلتر (SQL WHERE clause)
        
        Returns:
            تعداد records منتقل شده
        """
        # TODO: پیاده‌سازی migration
        logger.info(f"Migrating data from shard {from_shard} to shard {to_shard}")
        return 0


# Singleton instance
_shard_manager: Optional[DatabaseShardManager] = None


def init_shard_manager(
    shard_configs: List[Dict[str, str]],
    sharding_key: str = "patient_id",
    strategy: str = ShardingStrategy.HASH
) -> DatabaseShardManager:
    """مقداردهی اولیه shard manager"""
    global _shard_manager
    _shard_manager = DatabaseShardManager(shard_configs, sharding_key, strategy)
    return _shard_manager


def get_shard_manager() -> Optional[DatabaseShardManager]:
    """دریافت instance shard manager"""
    return _shard_manager

