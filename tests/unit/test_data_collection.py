"""
Unit Tests for Data Collection Service
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from cloud.services.data_collection.app.main import app
from cloud.services.data_collection.app.validators import validate_sensor_data
from cloud.services.data_collection.app.models import SensorDataRequest


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture
def sample_sensor_data():
    """Sample sensor data"""
    return SensorDataRequest(
        patient_id="patient-123",
        device_id="device-456",
        timestamp=datetime.now(),
        eeg_data=[[1.0, 2.0, 3.0] for _ in range(32)],  # 32 channels
        biomarker_values={"IL6": 10.5, "TNF_alpha": 8.2},
        physiological_params={"temperature": 36.5, "heart_rate": 72}
    )


class TestValidators:
    """Tests for validators"""
    
    def test_validate_sensor_data_valid(self, sample_sensor_data):
        """Test validation with valid data"""
        result = validate_sensor_data(sample_sensor_data)
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_sensor_data_missing_patient_id(self):
        """Test validation with missing patient_id"""
        data = SensorDataRequest(
            patient_id="",
            device_id="device-456",
            timestamp=datetime.now()
        )
        result = validate_sensor_data(data)
        assert result["valid"] is False
        assert "patient_id is required" in result["errors"]
    
    def test_validate_sensor_data_missing_device_id(self):
        """Test validation with missing device_id"""
        data = SensorDataRequest(
            patient_id="patient-123",
            device_id="",
            timestamp=datetime.now()
        )
        result = validate_sensor_data(data)
        assert result["valid"] is False
        assert "device_id is required" in result["errors"]
    
    def test_validate_sensor_data_invalid_eeg_structure(self):
        """Test validation with invalid EEG structure"""
        data = SensorDataRequest(
            patient_id="patient-123",
            device_id="device-456",
            timestamp=datetime.now(),
            eeg_data="invalid"  # Should be list
        )
        result = validate_sensor_data(data)
        assert result["valid"] is False
        assert "eeg_data must be a list" in result["errors"]
    
    def test_validate_sensor_data_inconsistent_eeg_channels(self):
        """Test validation with inconsistent EEG channel lengths"""
        data = SensorDataRequest(
            patient_id="patient-123",
            device_id="device-456",
            timestamp=datetime.now(),
            eeg_data=[[1.0, 2.0], [3.0]]  # Inconsistent lengths
        )
        result = validate_sensor_data(data)
        assert result["valid"] is False
        assert any("inconsistent length" in error for error in result["errors"])
    
    def test_validate_sensor_data_invalid_biomarker_type(self):
        """Test validation with invalid biomarker type"""
        data = SensorDataRequest(
            patient_id="patient-123",
            device_id="device-456",
            timestamp=datetime.now(),
            biomarker_values={"IL6": "invalid"}  # Should be number
        )
        result = validate_sensor_data(data)
        assert result["valid"] is False
        assert any("must be a number" in error for error in result["errors"])


class TestEndpoints:
    """Tests for API endpoints"""
    
    @patch('cloud.services.data_collection.app.main.get_db')
    @patch('cloud.services.data_collection.app.main.publish_sensor_data')
    def test_collect_sensor_data_success(
        self,
        mock_publish,
        mock_get_db,
        client,
        sample_sensor_data
    ):
        """Test successful data collection"""
        # Mock database
        mock_db = AsyncMock()
        mock_patient = Mock()
        mock_patient.id = "patient-123"
        mock_db.get = AsyncMock(return_value=mock_patient)
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Mock sensor data
        mock_sensor_data = Mock()
        mock_sensor_data.id = "data-123"
        mock_db.add.return_value = mock_sensor_data
        
        response = client.post(
            "/data/sensor",
            json=sample_sensor_data.dict()
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["data_id"] is not None
    
    @patch('cloud.services.data_collection.app.main.get_db')
    def test_collect_sensor_data_patient_not_found(
        self,
        mock_get_db,
        client,
        sample_sensor_data
    ):
        """Test data collection with non-existent patient"""
        # Mock database
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db
        
        response = client.post(
            "/data/sensor",
            json=sample_sensor_data.dict()
        )
        
        assert response.status_code == 404
        assert "Patient not found" in response.json()["detail"]
    
    def test_collect_sensor_data_invalid_data(self, client):
        """Test data collection with invalid data"""
        invalid_data = {
            "patient_id": "",  # Invalid
            "device_id": "device-456",
            "timestamp": datetime.now().isoformat()
        }
        
        response = client.post(
            "/data/sensor",
            json=invalid_data
        )
        
        assert response.status_code == 400
        assert "Invalid sensor data" in response.json()["detail"]
    
    @patch('cloud.services.data_collection.app.main.get_db')
    def test_get_sensor_data(
        self,
        mock_get_db,
        client
    ):
        """Test getting sensor data"""
        # Mock database
        mock_db = AsyncMock()
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = AsyncMock(return_value=[])
        mock_db.query = Mock(return_value=mock_query)
        mock_get_db.return_value = mock_db
        
        response = client.get("/data/sensor/patient-123")
        
        assert response.status_code == 200
        assert response.json()["patient_id"] == "patient-123"
        assert response.json()["count"] == 0
    
    @patch('cloud.services.data_collection.app.main.get_db')
    def test_get_sensor_stats(
        self,
        mock_get_db,
        client
    ):
        """Test getting sensor statistics"""
        # Mock database
        mock_db = AsyncMock()
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = AsyncMock(return_value=[])
        mock_db.query = Mock(return_value=mock_query)
        mock_get_db.return_value = mock_db
        
        response = client.get("/data/sensor/stats/patient-123?days=7")
        
        assert response.status_code == 200
        assert response.json()["patient_id"] == "patient-123"
        assert response.json()["period_days"] == 7


class TestHealthCheck:
    """Tests for health check"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "data-collection"

