"""
Database Service
سرویس بهینه‌سازی و مدیریت پایگاه داده
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from loguru import logger

from sqlalchemy.orm import Session
from ..shared.database_optimization import DatabaseOptimizer
from ..shared.read_replica import get_replica_manager, ReadReplicaManager
from ..shared.query_optimizer import QueryOptimizer
from ..user-management.app.database import get_db

app = FastAPI(
    title="Database Service",
    description="سرویس بهینه‌سازی و مدیریت پایگاه داده",
    version="1.0.0"
)


class IndexRequest(BaseModel):
    """درخواست ایجاد index"""
    table_name: str
    columns: List[str]
    unique: bool = False
    index_type: str = "btree"  # btree, hash, gin, gist


class PartitionRequest(BaseModel):
    """درخواست partitioning"""
    table_name: str
    partition_column: str
    partition_type: str = "range"  # range, list, hash


class QueryAnalysisRequest(BaseModel):
    """درخواست تحلیل query"""
    query: str
    params: Optional[Dict] = None


@app.post("/indexes/create")
async def create_index(request: IndexRequest, db: Session = Depends(get_db)):
    """ایجاد index"""
    try:
        optimizer = DatabaseOptimizer(db)
        
        if len(request.columns) == 1:
            success = optimizer.create_indexes(
                request.table_name,
                request.columns,
                request.unique
            )
        else:
            success = optimizer.create_composite_index(
                request.table_name,
                request.columns,
                request.index_type
            )
        
        if success:
            return {"status": "created", "table": request.table_name}
        else:
            raise HTTPException(500, "Failed to create index")
    
    except Exception as e:
        logger.error(f"Error creating index: {e}")
        raise HTTPException(500, str(e))


@app.get("/indexes/stats/{table_name}")
async def get_index_stats(table_name: str, db: Session = Depends(get_db)):
    """دریافت آمار index‌ها"""
    try:
        optimizer = DatabaseOptimizer(db)
        stats = optimizer.get_index_usage_stats(table_name)
        return {"table": table_name, "indexes": stats}
    
    except Exception as e:
        logger.error(f"Error getting index stats: {e}")
        raise HTTPException(500, str(e))


@app.post("/partitions/create")
async def create_partition(request: PartitionRequest, db: Session = Depends(get_db)):
    """ایجاد partitioned table"""
    try:
        optimizer = DatabaseOptimizer(db)
        success = optimizer.create_partitioned_table(
            request.table_name,
            request.partition_column,
            request.partition_type
        )
        
        if success:
            return {"status": "created", "table": request.table_name}
        else:
            raise HTTPException(500, "Failed to create partition")
    
    except Exception as e:
        logger.error(f"Error creating partition: {e}")
        raise HTTPException(500, str(e))


@app.post("/partitions/archive")
async def archive_partitions(
    table_name: str,
    older_than_days: int = 365,
    db: Session = Depends(get_db)
):
    """آرشیو partitions قدیمی"""
    try:
        optimizer = DatabaseOptimizer(db)
        archived = optimizer.archive_old_partitions(table_name, older_than_days)
        return {"archived": archived, "count": len(archived)}
    
    except Exception as e:
        logger.error(f"Error archiving partitions: {e}")
        raise HTTPException(500, str(e))


@app.post("/queries/analyze")
async def analyze_query(request: QueryAnalysisRequest, db: Session = Depends(get_db)):
    """تحلیل query"""
    try:
        optimizer = QueryOptimizer(db)
        result = optimizer.analyze_query_performance(request.query, request.params)
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing query: {e}")
        raise HTTPException(500, str(e))


@app.get("/queries/slow")
async def get_slow_queries(min_duration_ms: float = 100.0, db: Session = Depends(get_db)):
    """دریافت queries کند"""
    try:
        optimizer = DatabaseOptimizer(db)
        slow_queries = optimizer.get_slow_queries(min_duration_ms)
        return {"slow_queries": slow_queries}
    
    except Exception as e:
        logger.error(f"Error getting slow queries: {e}")
        raise HTTPException(500, str(e))


@app.post("/maintenance/vacuum/{table_name}")
async def vacuum_table(table_name: str, analyze: bool = True, db: Session = Depends(get_db)):
    """اجرای VACUUM"""
    try:
        optimizer = DatabaseOptimizer(db)
        success = optimizer.vacuum_table(table_name, analyze)
        
        if success:
            return {"status": "completed", "table": table_name}
        else:
            raise HTTPException(500, "Failed to vacuum table")
    
    except Exception as e:
        logger.error(f"Error vacuuming table: {e}")
        raise HTTPException(500, str(e))


@app.get("/replicas/stats")
async def get_replica_stats():
    """دریافت آمار replicas"""
    try:
        replica_manager = get_replica_manager()
        if not replica_manager:
            raise HTTPException(503, "Replica manager not initialized")
        
        stats = replica_manager.get_replica_stats()
        return {"replicas": stats}
    
    except Exception as e:
        logger.error(f"Error getting replica stats: {e}")
        raise HTTPException(500, str(e))


@app.post("/replicas/health-check")
async def check_replicas_health():
    """بررسی سلامت replicas"""
    try:
        replica_manager = get_replica_manager()
        if not replica_manager:
            raise HTTPException(503, "Replica manager not initialized")
        
        replica_manager.check_all_replicas_health()
        stats = replica_manager.get_replica_stats()
        
        return {"status": "checked", "replicas": stats}
    
    except Exception as e:
        logger.error(f"Error checking replica health: {e}")
        raise HTTPException(500, str(e))


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Database Service",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)

