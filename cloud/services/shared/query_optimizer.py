"""
Query Optimizer
بهینه‌سازی queries
"""

from typing import Dict, List, Optional, Any
from sqlalchemy import text, func
from sqlalchemy.orm import Query, Session
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
import re


class QueryOptimizer:
    """بهینه‌کننده queries"""
    
    def __init__(self, db_session: Session):
        """
        مقداردهی اولیه
        
        Args:
            db_session: SQLAlchemy session
        """
        self.db = db_session
    
    def optimize_select_query(self, query: Query, limit: Optional[int] = None,
                             offset: Optional[int] = None) -> Query:
        """
        بهینه‌سازی SELECT query
        
        Args:
            query: SQLAlchemy Query
            limit: محدودیت تعداد نتایج
            offset: offset برای pagination
        
        Returns:
            Query بهینه‌سازی شده
        """
        # اضافه کردن LIMIT
        if limit:
            query = query.limit(limit)
        
        # اضافه کردن OFFSET
        if offset:
            query = query.offset(offset)
        
        # استفاده از eager loading برای جلوگیری از N+1 queries
        # TODO: اضافه کردن joinedload یا selectinload
        
        return query
    
    def add_pagination(self, query: Query, page: int, page_size: int) -> Query:
        """
        اضافه کردن pagination
        
        Args:
            query: SQLAlchemy Query
            page: شماره صفحه (1-based)
            page_size: اندازه صفحه
        
        Returns:
            Query با pagination
        """
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size)
    
    def optimize_join_query(self, query: Query, use_inner_join: bool = True) -> Query:
        """
        بهینه‌سازی JOIN queries
        
        Args:
            query: SQLAlchemy Query
            use_inner_join: استفاده از INNER JOIN به جای LEFT JOIN
        
        Returns:
            Query بهینه‌سازی شده
        """
        # INNER JOIN سریع‌تر از LEFT JOIN است
        # اما باید مطمئن شویم که داده‌های NULL نداریم
        # TODO: تبدیل LEFT JOIN به INNER JOIN در صورت امکان
        
        return query
    
    def use_index_hint(self, query: str, table_name: str, index_name: str) -> str:
        """
        اضافه کردن index hint به query
        
        Args:
            query: SQL query string
            table_name: نام جدول
            index_name: نام index
        
        Returns:
            Query با index hint
        """
        # PostgreSQL syntax: /*+ Index(table index) */
        hint = f"/*+ Index({table_name} {index_name}) */"
        
        # اضافه کردن hint بعد از SELECT
        if query.upper().strip().startswith("SELECT"):
            query = query.replace("SELECT", f"SELECT {hint}", 1)
        
        return query
    
    def analyze_query_performance(self, query: str, params: Optional[Dict] = None) -> Dict:
        """
        تحلیل عملکرد query
        
        Args:
            query: SQL query
            params: پارامترهای query
        
        Returns:
            آمار عملکرد
        """
        try:
            # EXPLAIN ANALYZE
            explain_query = text(f"EXPLAIN (ANALYZE, BUFFERS, VERBOSE) {query}")
            result = self.db.execute(explain_query, params or {})
            
            plan_lines = []
            total_cost = 0.0
            execution_time = 0.0
            
            for row in result:
                plan_line = row[0]
                plan_lines.append(plan_line)
                
                # استخراج cost
                cost_match = re.search(r'cost=([\d.]+)\.\.([\d.]+)', plan_line)
                if cost_match:
                    total_cost = max(total_cost, float(cost_match.group(2)))
                
                # استخراج execution time
                time_match = re.search(r'Execution Time: ([\d.]+)', plan_line)
                if time_match:
                    execution_time = float(time_match.group(1))
            
            return {
                "query": query,
                "plan": "\n".join(plan_lines),
                "estimated_cost": total_cost,
                "execution_time_ms": execution_time,
                "optimization_suggestions": self._get_optimization_suggestions(plan_lines)
            }
        
        except SQLAlchemyError as e:
            logger.error(f"Error analyzing query: {e}")
            return {"error": str(e)}
    
    def _get_optimization_suggestions(self, plan_lines: List[str]) -> List[str]:
        """دریافت پیشنهادات بهینه‌سازی از query plan"""
        suggestions = []
        
        plan_text = "\n".join(plan_lines).upper()
        
        # بررسی Sequential Scan
        if "SEQ SCAN" in plan_text:
            suggestions.append("Consider adding an index to avoid sequential scan")
        
        # بررسی Nested Loop
        if "NESTED LOOP" in plan_text and "cost=" in plan_text:
            # استخراج cost
            cost_match = re.search(r'cost=([\d.]+)\.\.([\d.]+)', plan_text)
            if cost_match:
                cost = float(cost_match.group(2))
                if cost > 1000:
                    suggestions.append("High cost nested loop - consider using hash join or merge join")
        
        # بررسی missing index
        if "FILTER" in plan_text and "SEQ SCAN" in plan_text:
            suggestions.append("Add index on filtered columns")
        
        # بررسی large result set
        if "LIMIT" not in plan_text and "COUNT" not in plan_text:
            suggestions.append("Consider adding LIMIT to reduce result set size")
        
        return suggestions
    
    def optimize_bulk_insert(self, table_name: str, data: List[Dict]) -> bool:
        """
        بهینه‌سازی bulk insert
        
        Args:
            table_name: نام جدول
            data: لیست داده‌ها
        
        Returns:
            True در صورت موفقیت
        """
        try:
            if not data:
                return True
            
            # استفاده از COPY برای bulk insert (سریع‌تر از INSERT)
            # یا استفاده از executemany
            
            # برای PostgreSQL، استفاده از unnest
            columns = list(data[0].keys())
            values_list = [tuple(row[col] for col in columns) for row in data]
            
            # ساخت query با VALUES
            placeholders = ", ".join(["%s"] * len(columns))
            columns_str = ", ".join(columns)
            
            query = f"""
                INSERT INTO {table_name} ({columns_str})
                VALUES {placeholders}
            """
            
            # استفاده از executemany
            self.db.execute(text(query), values_list)
            self.db.commit()
            
            logger.info(f"Bulk inserted {len(data)} rows into {table_name}")
            return True
        
        except SQLAlchemyError as e:
            logger.error(f"Error in bulk insert: {e}")
            self.db.rollback()
            return False
    
    def create_materialized_view(self, view_name: str, query: str, 
                                refresh_interval: Optional[int] = None):
        """
        ایجاد materialized view
        
        Args:
            view_name: نام view
            query: SQL query
            refresh_interval: فاصله refresh (seconds) - None برای manual refresh
        """
        try:
            create_query = text(f"""
                CREATE MATERIALIZED VIEW IF NOT EXISTS {view_name}
                AS {query}
            """)
            
            self.db.execute(create_query)
            self.db.commit()
            
            # ایجاد index روی materialized view
            self.db.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{view_name}_id ON {view_name}(id)"))
            self.db.commit()
            
            logger.info(f"Created materialized view {view_name}")
            
            # اگر refresh_interval مشخص شده، schedule refresh
            if refresh_interval:
                # TODO: استفاده از pg_cron یا scheduler
                pass
            
            return True
        
        except SQLAlchemyError as e:
            logger.error(f"Error creating materialized view: {e}")
            self.db.rollback()
            return False
    
    def refresh_materialized_view(self, view_name: str, concurrently: bool = True):
        """
        Refresh materialized view
        
        Args:
            view_name: نام view
            concurrently: آیا به صورت concurrent انجام شود
        """
        try:
            refresh_cmd = "REFRESH MATERIALIZED VIEW CONCURRENTLY" if concurrently else "REFRESH MATERIALIZED VIEW"
            query = text(f"{refresh_cmd} {view_name}")
            
            self.db.execute(query)
            self.db.commit()
            
            logger.info(f"Refreshed materialized view {view_name}")
            return True
        
        except SQLAlchemyError as e:
            logger.error(f"Error refreshing materialized view: {e}")
            self.db.rollback()
            return False

