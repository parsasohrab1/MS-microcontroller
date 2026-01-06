"""
Unit Tests for Analytics Service
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from cloud.services.analytics_service.app.main import app
from cloud.services.analytics_service.app.statistics import calculate_statistics, generate_report


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture
def sample_analytics_request():
    """Sample analytics request"""
    return {
        "patient_id": "patient-123",
        "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
        "end_date": datetime.now().isoformat(),
        "metrics": ["accuracy", "f1"]
    }


class TestStatistics:
    """Tests for statistics functions"""
    
    @pytest.mark.asyncio
    async def test_calculate_statistics(self):
        """Test statistics calculation"""
        mock_db = AsyncMock()
        
        stats = await calculate_statistics(
            patient_id="patient-123",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            metrics=["accuracy", "f1"],
            db=mock_db
        )
        
        assert isinstance(stats, dict)
        assert "total_predictions" in stats
        assert "attack_predictions" in stats
        assert "avg_confidence" in stats
    
    @pytest.mark.asyncio
    async def test_generate_report(self):
        """Test report generation"""
        mock_db = AsyncMock()
        
        report = await generate_report(
            patient_id="patient-123",
            report_type="daily",
            format="json",
            db=mock_db
        )
        
        assert isinstance(report, dict)
        assert report["patient_id"] == "patient-123"
        assert report["report_type"] == "daily"
        assert report["format"] == "json"


class TestEndpoints:
    """Tests for API endpoints"""
    
    @patch('cloud.services.analytics_service.app.main.get_from_cache')
    @patch('cloud.services.analytics_service.app.main.calculate_statistics')
    @patch('cloud.services.analytics_service.app.main.calculate_trends')
    @patch('cloud.services.analytics_service.app.main.set_to_cache')
    @pytest.mark.asyncio
    async def test_get_analytics(
        self,
        mock_set_cache,
        mock_trends,
        mock_stats,
        mock_get_cache,
        client,
        sample_analytics_request
    ):
        """Test getting analytics"""
        # Mock cache miss
        mock_get_cache.return_value = None
        
        # Mock statistics
        mock_stats.return_value = {
            "total_predictions": 100,
            "attack_predictions": 10,
            "avg_confidence": 0.95
        }
        
        # Mock trends
        mock_trends.return_value = {
            "attack_frequency": "stable",
            "confidence_trend": "increasing"
        }
        
        response = client.post(
            "/analytics",
            json=sample_analytics_request
        )
        
        assert response.status_code == 200
        assert response.json()["patient_id"] == "patient-123"
        assert "statistics" in response.json()
        assert "trends" in response.json()
    
    @patch('cloud.services.analytics_service.app.main.get_from_cache')
    @pytest.mark.asyncio
    async def test_get_analytics_cached(
        self,
        mock_get_cache,
        client,
        sample_analytics_request
    ):
        """Test getting cached analytics"""
        # Mock cache hit
        cached_result = {
            "patient_id": "patient-123",
            "period": {},
            "statistics": {"total_predictions": 100},
            "trends": {},
            "generated_at": datetime.now().isoformat()
        }
        mock_get_cache.return_value = cached_result
        
        response = client.post(
            "/analytics",
            json=sample_analytics_request
        )
        
        assert response.status_code == 200
        assert response.json()["patient_id"] == "patient-123"
    
    @patch('cloud.services.analytics_service.app.main.generate_report')
    @pytest.mark.asyncio
    async def test_generate_report_endpoint(
        self,
        mock_generate_report,
        client
    ):
        """Test report generation endpoint"""
        mock_report = {
            "patient_id": "patient-123",
            "report_type": "daily",
            "format": "json",
            "generated_at": datetime.now().isoformat(),
            "data": {}
        }
        mock_generate_report.return_value = mock_report
        
        response = client.post(
            "/report",
            json={
                "patient_id": "patient-123",
                "report_type": "daily",
                "format": "json"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["patient_id"] == "patient-123"
    
    @patch('cloud.services.analytics_service.app.main.get_analytics')
    @pytest.mark.asyncio
    async def test_get_patient_summary(
        self,
        mock_get_analytics,
        client
    ):
        """Test getting patient summary"""
        mock_analytics = {
            "patient_id": "patient-123",
            "statistics": {
                "total_predictions": 100,
                "attack_predictions": 10,
                "avg_confidence": 0.95
            },
            "trends": {
                "attack_frequency": "stable"
            },
            "generated_at": datetime.now()
        }
        mock_get_analytics.return_value = mock_analytics
        
        response = client.get("/analytics/patient/patient-123/summary?days=30")
        
        assert response.status_code == 200
        assert response.json()["patient_id"] == "patient-123"
        assert "key_metrics" in response.json()


class TestHealthCheck:
    """Tests for health check"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "analytics"

