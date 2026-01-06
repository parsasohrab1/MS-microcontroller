"""
Integration Tests for Data Collection Service
"""

import pytest
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cloud.services.data_collection.app.main import app
from cloud.services.data_collection.app.database import Base, get_db
from cloud.services.data_collection.app.models import Patient, SensorData


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_patient(db_session):
    """Create sample patient"""
    patient = Patient(
        id="patient-123",
        email="test@example.com",
        full_name="Test User",
        created_at=datetime.now()
    )
    db_session.add(patient)
    db_session.commit()
    return patient


class TestDataCollectionIntegration:
    """Integration tests for data collection"""
    
    def test_collect_and_retrieve_sensor_data(
        self,
        client,
        sample_patient
    ):
        """Test collecting and retrieving sensor data"""
        # Collect data
        sensor_data = {
            "patient_id": "patient-123",
            "device_id": "device-456",
            "timestamp": datetime.now().isoformat(),
            "biomarker_values": {"IL6": 10.5, "TNF_alpha": 8.2},
            "physiological_params": {"temperature": 36.5, "heart_rate": 72}
        }
        
        response = client.post("/data/sensor", json=sensor_data)
        assert response.status_code == 200
        assert response.json()["success"] is True
        data_id = response.json()["data_id"]
        
        # Retrieve data
        response = client.get("/data/sensor/patient-123")
        assert response.status_code == 200
        assert response.json()["count"] > 0
        assert any(d["id"] == data_id for d in response.json()["data"])
    
    def test_batch_data_collection(
        self,
        client,
        sample_patient
    ):
        """Test batch data collection"""
        batch_data = {
            "data": [
                {
                    "patient_id": "patient-123",
                    "device_id": "device-456",
                    "timestamp": datetime.now().isoformat(),
                    "biomarker_values": {"IL6": 10.5}
                },
                {
                    "patient_id": "patient-123",
                    "device_id": "device-456",
                    "timestamp": datetime.now().isoformat(),
                    "biomarker_values": {"IL6": 11.0}
                }
            ]
        }
        
        response = client.post("/data/sensor/batch", json=batch_data)
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert all(r["success"] for r in response.json())
    
    def test_get_sensor_statistics(
        self,
        client,
        sample_patient
    ):
        """Test getting sensor statistics"""
        # Collect some data first
        for i in range(5):
            sensor_data = {
                "patient_id": "patient-123",
                "device_id": "device-456",
                "timestamp": datetime.now().isoformat(),
                "biomarker_values": {"IL6": 10.0 + i}
            }
            client.post("/data/sensor", json=sensor_data)
        
        # Get statistics
        response = client.get("/data/sensor/stats/patient-123?days=7")
        assert response.status_code == 200
        assert response.json()["total_records"] >= 5
        assert "biomarker_stats" in response.json()

