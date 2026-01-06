"""
Performance Tests with Locust
تست‌های عملکرد با Locust
"""

from locust import HttpUser, task, between
import random


class MSNeuroplatformUser(HttpUser):
    """User class برای performance testing"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Actions before starting"""
        # Login
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.client.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def get_patient_data(self):
        """Get patient data"""
        patient_id = f"patient_{random.randint(1, 100)}"
        self.client.get(f"/api/v1/patients/{patient_id}")
    
    @task(2)
    def get_sensor_data(self):
        """Get sensor data"""
        patient_id = f"patient_{random.randint(1, 100)}"
        self.client.get(f"/api/v1/data/sensor/{patient_id}")
    
    @task(1)
    def get_predictions(self):
        """Get predictions"""
        patient_id = f"patient_{random.randint(1, 100)}"
        self.client.get(f"/api/v1/ml/predictions/{patient_id}")
    
    @task(1)
    def create_symptom(self):
        """Create symptom"""
        self.client.post("/api/v1/symptoms", json={
            "patient_id": f"patient_{random.randint(1, 100)}",
            "type": "headache",
            "severity": random.randint(1, 10),
            "notes": "Test symptom"
        })
    
    @task(1)
    def health_check(self):
        """Health check"""
        self.client.get("/health")

