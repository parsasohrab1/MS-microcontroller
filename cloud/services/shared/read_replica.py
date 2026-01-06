"""
Read Replica Manager
مدیریت Read Replicas برای بهبود کارایی
"""

from typing import Optional, List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from loguru import logger
import random
import time


class ReadReplicaManager:
    """مدیریت Read Replicas"""
    
    def __init__(self, primary_db_url: str, replica_urls: List[str]):
        """
        مقداردهی اولیه
        
        Args:
            primary_db_url: URL پایگاه داده اصلی
            replica_urls: لیست URL های replica
        """
        self.primary_url = primary_db_url
        self.replica_urls = replica_urls
        
        # ایجاد engines
        self.primary_engine = create_engine(
            primary_db_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
        
        self.replica_engines = []
        for url in replica_urls:
            engine = create_engine(
                url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            )
            self.replica_engines.append(engine)
        
        # Session factories
        self.primary_session = sessionmaker(bind=self.primary_engine)
        self.replica_sessions = [
            sessionmaker(bind=engine) for engine in self.replica_engines
        ]
        
        # Health check
        self.replica_health = [True] * len(replica_urls)
        self.last_health_check = [0.0] * len(replica_urls)
    
    def get_read_session(self) -> Session:
        """
        دریافت session برای read operations
        
        Returns:
            Session از replica (یا primary در صورت عدم دسترسی)
        """
        # انتخاب replica سالم
        healthy_replicas = [
            i for i, healthy in enumerate(self.replica_health) if healthy
        ]
        
        if healthy_replicas:
            # انتخاب تصادفی از replicas سالم
            replica_idx = random.choice(healthy_replicas)
            return self.replica_sessions[replica_idx]()
        else:
            # Fallback به primary
            logger.warning("No healthy replicas, using primary for read")
            return self.primary_session()
    
    def get_write_session(self) -> Session:
        """
        دریافت session برای write operations
        
        Returns:
            Session از primary
        """
        return self.primary_session()
    
    @contextmanager
    def read_session(self):
        """
        Context manager برای read session
        
        Usage:
            with replica_manager.read_session() as session:
                result = session.query(Model).all()
        """
        session = self.get_read_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Read session error: {e}")
            raise
        finally:
            session.close()
    
    @contextmanager
    def write_session(self):
        """
        Context manager برای write session
        
        Usage:
            with replica_manager.write_session() as session:
                session.add(new_object)
        """
        session = self.get_write_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Write session error: {e}")
            raise
        finally:
            session.close()
    
    def check_replica_health(self, replica_idx: int) -> bool:
        """
        بررسی سلامت replica
        
        Args:
            replica_idx: index replica
        
        Returns:
            True اگر سالم است
        """
        if replica_idx >= len(self.replica_engines):
            return False
        
        try:
            engine = self.replica_engines[replica_idx]
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.scalar()
            
            self.replica_health[replica_idx] = True
            self.last_health_check[replica_idx] = time.time()
            return True
        
        except Exception as e:
            logger.error(f"Replica {replica_idx} health check failed: {e}")
            self.replica_health[replica_idx] = False
            return False
    
    def check_all_replicas_health(self):
        """بررسی سلامت همه replicas"""
        for i in range(len(self.replica_engines)):
            self.check_replica_health(i)
    
    def get_replica_stats(self) -> List[Dict]:
        """
        دریافت آمار replicas
        
        Returns:
            لیست آمار replicas
        """
        stats = []
        
        for i, engine in enumerate(self.replica_engines):
            try:
                with engine.connect() as conn:
                    # دریافت lag
                    lag_query = text("""
                        SELECT EXTRACT(EPOCH FROM (NOW() - pg_last_xact_replay_timestamp())) * 1000
                    """)
                    result = conn.execute(lag_query)
                    lag_ms = result.scalar() or 0
                    
                    # دریافت تعداد connections
                    conn_query = text("""
                        SELECT count(*) 
                        FROM pg_stat_activity 
                        WHERE datname = current_database()
                    """)
                    result = conn.execute(conn_query)
                    connections = result.scalar() or 0
                
                stats.append({
                    "replica_index": i,
                    "healthy": self.replica_health[i],
                    "lag_ms": lag_ms,
                    "connections": connections,
                    "last_health_check": self.last_health_check[i]
                })
            
            except Exception as e:
                stats.append({
                    "replica_index": i,
                    "healthy": False,
                    "error": str(e)
                })
        
        return stats
    
    def get_load_balanced_session(self) -> Session:
        """
        دریافت session با load balancing
        
        Returns:
            Session از replica با کمترین load
        """
        # انتخاب replica با کمترین lag
        stats = self.get_replica_stats()
        healthy_stats = [s for s in stats if s.get("healthy", False)]
        
        if healthy_stats:
            # انتخاب replica با کمترین lag
            best_replica = min(healthy_stats, key=lambda x: x.get("lag_ms", float('inf')))
            return self.replica_sessions[best_replica["replica_index"]]()
        else:
            # Fallback به primary
            return self.primary_session()


# Singleton instance
_replica_manager: Optional[ReadReplicaManager] = None


def init_replica_manager(primary_url: str, replica_urls: List[str]):
    """مقداردهی اولیه replica manager"""
    global _replica_manager
    _replica_manager = ReadReplicaManager(primary_url, replica_urls)
    return _replica_manager


def get_replica_manager() -> Optional[ReadReplicaManager]:
    """دریافت instance replica manager"""
    return _replica_manager

