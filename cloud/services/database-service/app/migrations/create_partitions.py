"""
Migration: ایجاد partitions برای داده‌های قدیمی
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta


def upgrade():
    """ایجاد partitioned tables"""
    
    # ایجاد partitioned table برای sensor_data
    op.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id SERIAL,
            patient_id VARCHAR(255) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            data JSONB,
            PRIMARY KEY (id, timestamp)
        ) PARTITION BY RANGE (timestamp)
    """)
    
    # ایجاد partitions برای 12 ماه گذشته و 12 ماه آینده
    for i in range(-12, 13):
        partition_date = datetime.now() + timedelta(days=30 * i)
        partition_name = f"sensor_data_{partition_date.strftime('%Y_%m')}"
        
        start_date = partition_date.replace(day=1)
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)
        
        op.execute(f"""
            CREATE TABLE IF NOT EXISTS {partition_name}
            PARTITION OF sensor_data
            FOR VALUES FROM ('{start_date.isoformat()}') 
            TO ('{end_date.isoformat()}')
        """)
    
    # ایجاد partitioned table برای predictions
    op.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL,
            patient_id VARCHAR(255) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            prediction_result JSONB,
            PRIMARY KEY (id, timestamp)
        ) PARTITION BY RANGE (timestamp)
    """)
    
    # ایجاد partitions برای predictions
    for i in range(-12, 13):
        partition_date = datetime.now() + timedelta(days=30 * i)
        partition_name = f"predictions_{partition_date.strftime('%Y_%m')}"
        
        start_date = partition_date.replace(day=1)
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)
        
        op.execute(f"""
            CREATE TABLE IF NOT EXISTS {partition_name}
            PARTITION OF predictions
            FOR VALUES FROM ('{start_date.isoformat()}') 
            TO ('{end_date.isoformat()}')
        """)


def downgrade():
    """حذف partitions"""
    # حذف partitions
    for i in range(-12, 13):
        partition_date = datetime.now() + timedelta(days=30 * i)
        partition_name = f"sensor_data_{partition_date.strftime('%Y_%m')}"
        op.execute(f"DROP TABLE IF EXISTS {partition_name}")
        
        partition_name = f"predictions_{partition_date.strftime('%Y_%m')}"
        op.execute(f"DROP TABLE IF EXISTS {partition_name}")
    
    # حذف parent tables
    op.execute("DROP TABLE IF EXISTS sensor_data")
    op.execute("DROP TABLE IF EXISTS predictions")

