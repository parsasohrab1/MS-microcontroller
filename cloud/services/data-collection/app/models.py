"""
Database Models for Data Collection Service
"""

from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class Patient(Base):
    """مدل بیمار"""
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    created_at = Column(DateTime)


class SensorData(Base):
    """مدل داده سنسور"""
    __tablename__ = "sensor_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), index=True)
    device_id = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    eeg_data = Column(JSON)  # Store as JSON
    biomarker_values = Column(JSON)
    physiological_params = Column(JSON)
    metadata = Column(JSON)
    created_at = Column(DateTime)

