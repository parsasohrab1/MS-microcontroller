"""
Pytest Configuration and Shared Fixtures
"""

import pytest
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Add services to path
services_path = os.path.join(project_root, 'cloud', 'services')
sys.path.insert(0, services_path)


@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "database_url": os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db"),
        "redis_url": os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1"),
        "rabbitmq_url": os.getenv("TEST_RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"),
    }


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables"""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

