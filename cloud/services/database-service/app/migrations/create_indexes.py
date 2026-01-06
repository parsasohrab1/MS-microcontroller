"""
Migration: ایجاد indexes بهینه
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    """ایجاد indexes"""
    
    # Indexes برای جدول users
    op.create_index(
        'idx_users_email',
        'users',
        ['email'],
        unique=True
    )
    
    op.create_index(
        'idx_users_created_at',
        'users',
        ['created_at']
    )
    
    # Composite index برای جستجوی کاربران
    op.create_index(
        'idx_users_email_name',
        'users',
        ['email', 'name']
    )
    
    # Indexes برای جدول sensor_data (فرضی)
    op.create_index(
        'idx_sensor_data_patient_timestamp',
        'sensor_data',
        ['patient_id', 'timestamp']
    )
    
    op.create_index(
        'idx_sensor_data_timestamp',
        'sensor_data',
        ['timestamp']
    )
    
    # Index برای جدول predictions
    op.create_index(
        'idx_predictions_patient_timestamp',
        'predictions',
        ['patient_id', 'timestamp']
    )
    
    # GIN index برای JSONB columns
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_sensor_data_data_gin 
        ON sensor_data USING gin (data)
    """)


def downgrade():
    """حذف indexes"""
    op.drop_index('idx_users_email', table_name='users')
    op.drop_index('idx_users_created_at', table_name='users')
    op.drop_index('idx_users_email_name', table_name='users')
    op.drop_index('idx_sensor_data_patient_timestamp', table_name='sensor_data')
    op.drop_index('idx_sensor_data_timestamp', table_name='sensor_data')
    op.drop_index('idx_predictions_patient_timestamp', table_name='predictions')
    op.execute("DROP INDEX IF EXISTS idx_sensor_data_data_gin")

