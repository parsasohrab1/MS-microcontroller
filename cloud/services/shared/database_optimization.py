"""
Database Optimization
بهینه‌سازی کارایی پایگاه داده
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import Index, text, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
import json


class DatabaseOptimizer:
    """بهینه‌کننده پایگاه داده"""
    
    def __init__(self, db_session: Session):
        """
        مقداردهی اولیه
        
        Args:
            db_session: SQLAlchemy session
        """
        self.db = db_session
    
    # ========================================================================
    # Indexing
    # ========================================================================
    
    def create_indexes(self, table_name: str, columns: List[str], unique: bool = False):
        """
        ایجاد index برای جدول
        
        Args:
            table_name: نام جدول
            columns: لیست ستون‌ها
            unique: آیا index باید unique باشد
        """
        try:
            index_name = f"idx_{table_name}_{'_'.join(columns)}"
            
            if unique:
                index_name = f"idx_{table_name}_{'_'.join(columns)}_unique"
            
            # بررسی وجود index
            check_query = text(f"""
                SELECT COUNT(*) 
                FROM pg_indexes 
                WHERE indexname = :index_name
            """)
            
            result = self.db.execute(check_query, {"index_name": index_name})
            exists = result.scalar() > 0
            
            if exists:
                logger.info(f"Index {index_name} already exists")
                return True
            
            # ایجاد index
            columns_str = ", ".join(columns)
            unique_str = "UNIQUE" if unique else ""
            
            create_query = text(f"""
                CREATE {unique_str} INDEX IF NOT EXISTS {index_name}
                ON {table_name} ({columns_str})
            """)
            
            self.db.execute(create_query)
            self.db.commit()
            
            logger.info(f"Created index {index_name} on {table_name}({columns_str})")
            return True
        
        except SQLAlchemyError as e:
            logger.error(f"Error creating index: {e}")
            self.db.rollback()
            return False
    
    def create_composite_index(self, table_name: str, columns: List[str], 
                              index_type: str = "btree"):
        """
        ایجاد composite index
        
        Args:
            table_name: نام جدول
            columns: لیست ستون‌ها
            index_type: نوع index (btree, hash, gin, gist)
        """
        try:
            index_name = f"idx_{table_name}_{'_'.join(columns)}_composite"
            
            columns_str = ", ".join(columns)
            
            create_query = text(f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table_name} USING {index_type} ({columns_str})
            """)
            
            self.db.execute(create_query)
            self.db.commit()
            
            logger.info(f"Created composite {index_type} index {index_name}")
            return True
        
        except SQLAlchemyError as e:
            logger.error(f"Error creating composite index: {e}")
            self.db.rollback()
            return False
    
    def analyze_table(self, table_name: str):
        """
        اجرای ANALYZE برای بهینه‌سازی query planner
        
        Args:
            table_name: نام جدول
        """
        try:
            analyze_query = text(f"ANALYZE {table_name}")
            self.db.execute(analyze_query)
            self.db.commit()
            
            logger.info(f"Analyzed table {table_name}")
            return True
        
        except SQLAlchemyError as e:
            logger.error(f"Error analyzing table: {e}")
            return False
    
    def get_index_usage_stats(self, table_name: str) -> List[Dict]:
        """
        دریافت آمار استفاده از index
        
        Args:
            table_name: نام جدول
        
        Returns:
            لیست آمار index‌ها
        """
        try:
            query = text("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan as index_scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched
                FROM pg_stat_user_indexes
                WHERE tablename = :table_name
                ORDER BY idx_scan DESC
            """)
            
            result = self.db.execute(query, {"table_name": table_name})
            
            stats = []
            for row in result:
                stats.append({
                    "index_name": row.indexname,
                    "scans": row.index_scans,
                    "tuples_read": row.tuples_read,
                    "tuples_fetched": row.tuples_fetched
                })
            
            return stats
        
        except SQLAlchemyError as e:
            logger.error(f"Error getting index stats: {e}")
            return []
    
    # ========================================================================
    # Partitioning
    # ========================================================================
    
    def create_partitioned_table(self, table_name: str, partition_column: str,
                                 partition_type: str = "range"):
        """
        ایجاد partitioned table
        
        Args:
            table_name: نام جدول
            partition_column: ستون برای partitioning
            partition_type: نوع partitioning (range, list, hash)
        """
        try:
            # این یک مثال است - باید بر اساس schema واقعی تنظیم شود
            if partition_type == "range":
                # ایجاد parent table
                create_parent = text(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id SERIAL PRIMARY KEY,
                        {partition_column} TIMESTAMP NOT NULL,
                        data JSONB
                    ) PARTITION BY RANGE ({partition_column})
                """)
                
                self.db.execute(create_parent)
                
                # ایجاد partitions برای 12 ماه گذشته و آینده
                for i in range(-12, 13):
                    partition_date = datetime.now() + timedelta(days=30 * i)
                    partition_name = f"{table_name}_{partition_date.strftime('%Y_%m')}"
                    
                    start_date = partition_date.replace(day=1)
                    if start_date.month == 12:
                        end_date = start_date.replace(year=start_date.year + 1, month=1)
                    else:
                        end_date = start_date.replace(month=start_date.month + 1)
                    
                    create_partition = text(f"""
                        CREATE TABLE IF NOT EXISTS {partition_name}
                        PARTITION OF {table_name}
                        FOR VALUES FROM ('{start_date.isoformat()}') 
                        TO ('{end_date.isoformat()}')
                    """)
                    
                    self.db.execute(create_partition)
                
                self.db.commit()
                logger.info(f"Created partitioned table {table_name}")
                return True
            
            return False
        
        except SQLAlchemyError as e:
            logger.error(f"Error creating partitioned table: {e}")
            self.db.rollback()
            return False
    
    def create_partition_for_month(self, table_name: str, year: int, month: int):
        """
        ایجاد partition برای ماه مشخص
        
        Args:
            table_name: نام جدول
            year: سال
            month: ماه
        """
        try:
            partition_name = f"{table_name}_{year}_{month:02d}"
            start_date = datetime(year, month, 1)
            
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            create_partition = text(f"""
                CREATE TABLE IF NOT EXISTS {partition_name}
                PARTITION OF {table_name}
                FOR VALUES FROM ('{start_date.isoformat()}') 
                TO ('{end_date.isoformat()}')
            """)
            
            self.db.execute(create_partition)
            self.db.commit()
            
            logger.info(f"Created partition {partition_name}")
            return True
        
        except SQLAlchemyError as e:
            logger.error(f"Error creating partition: {e}")
            self.db.rollback()
            return False
    
    def archive_old_partitions(self, table_name: str, older_than_days: int = 365):
        """
        آرشیو partitions قدیمی
        
        Args:
            table_name: نام جدول
            older_than_days: partitions قدیمی‌تر از این تعداد روز
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            
            # پیدا کردن partitions قدیمی
            query = text("""
                SELECT tablename
                FROM pg_tables
                WHERE tablename LIKE :pattern
                AND schemaname = 'public'
            """)
            
            pattern = f"{table_name}_%"
            result = self.db.execute(query, {"pattern": pattern})
            
            archived = []
            for row in result:
                partition_name = row.tablename
                # استخراج تاریخ از نام partition
                try:
                    date_part = partition_name.split('_')[-2:]
                    year, month = int(date_part[0]), int(date_part[1])
                    partition_date = datetime(year, month, 1)
                    
                    if partition_date < cutoff_date:
                        # انتقال به archive schema
                        archive_query = text(f"""
                            ALTER TABLE {partition_name} 
                            SET SCHEMA archive
                        """)
                        
                        self.db.execute(archive_query)
                        archived.append(partition_name)
                
                except (ValueError, IndexError):
                    continue
            
            self.db.commit()
            
            if archived:
                logger.info(f"Archived {len(archived)} partitions: {archived}")
            
            return archived
        
        except SQLAlchemyError as e:
            logger.error(f"Error archiving partitions: {e}")
            self.db.rollback()
            return []
    
    # ========================================================================
    # Query Optimization
    # ========================================================================
    
    def explain_query(self, query: str, params: Optional[Dict] = None) -> Dict:
        """
        تحلیل query با EXPLAIN
        
        Args:
            query: SQL query
            params: پارامترهای query
        
        Returns:
            نتیجه EXPLAIN
        """
        try:
            explain_query = text(f"EXPLAIN ANALYZE {query}")
            result = self.db.execute(explain_query, params or {})
            
            plan = []
            for row in result:
                plan.append(row[0])
            
            return {
                "query": query,
                "plan": "\n".join(plan)
            }
        
        except SQLAlchemyError as e:
            logger.error(f"Error explaining query: {e}")
            return {"error": str(e)}
    
    def optimize_query(self, query: str, params: Optional[Dict] = None) -> str:
        """
        بهینه‌سازی query
        
        Args:
            query: SQL query
            params: پارامترهای query
        
        Returns:
            Query بهینه‌سازی شده
        """
        # این یک مثال ساده است
        # در واقعیت، باید از query planner استفاده شود
        
        optimized = query
        
        # حذف SELECT * و جایگزینی با ستون‌های مشخص
        if "SELECT *" in query.upper():
            # TODO: استخراج ستون‌های مورد نیاز
            pass
        
        # اضافه کردن LIMIT در صورت نیاز
        if "LIMIT" not in query.upper() and "COUNT" not in query.upper():
            # برای SELECT queries، اضافه کردن LIMIT
            if query.upper().strip().startswith("SELECT"):
                optimized = query.rstrip(";") + " LIMIT 1000"
        
        return optimized
    
    def get_slow_queries(self, min_duration_ms: float = 100.0) -> List[Dict]:
        """
        دریافت queries کند
        
        Args:
            min_duration_ms: حداقل زمان اجرا (ms)
        
        Returns:
            لیست queries کند
        """
        try:
            # استفاده از pg_stat_statements (نیاز به extension)
            query = text("""
                SELECT
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    max_exec_time
                FROM pg_stat_statements
                WHERE mean_exec_time > :min_duration
                ORDER BY mean_exec_time DESC
                LIMIT 50
            """)
            
            result = self.db.execute(query, {"min_duration": min_duration_ms})
            
            slow_queries = []
            for row in result:
                slow_queries.append({
                    "query": row.query[:200],  # محدود کردن طول
                    "calls": row.calls,
                    "total_time_ms": row.total_exec_time,
                    "mean_time_ms": row.mean_exec_time,
                    "max_time_ms": row.max_exec_time
                })
            
            return slow_queries
        
        except SQLAlchemyError as e:
            logger.warning(f"pg_stat_statements not available: {e}")
            return []
    
    # ========================================================================
    # Vacuum and Maintenance
    # ========================================================================
    
    def vacuum_table(self, table_name: str, analyze: bool = True):
        """
        اجرای VACUUM برای جدول
        
        Args:
            table_name: نام جدول
            analyze: آیا ANALYZE هم اجرا شود
        """
        try:
            vacuum_cmd = "VACUUM ANALYZE" if analyze else "VACUUM"
            query = text(f"{vacuum_cmd} {table_name}")
            
            self.db.execute(query)
            self.db.commit()
            
            logger.info(f"Vacuumed table {table_name}")
            return True
        
        except SQLAlchemyError as e:
            logger.error(f"Error vacuuming table: {e}")
            return False
    
    def reindex_table(self, table_name: str):
        """
        Rebuild indexes برای جدول
        
        Args:
            table_name: نام جدول
        """
        try:
            query = text(f"REINDEX TABLE {table_name}")
            self.db.execute(query)
            self.db.commit()
            
            logger.info(f"Reindexed table {table_name}")
            return True
        
        except SQLAlchemyError as e:
            logger.error(f"Error reindexing table: {e}")
            return False

