"""
HL7/FHIR Client
کلاینت برای کار با HL7/FHIR
"""

from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
import httpx
import json


class FHIRClient:
    """کلاینت FHIR"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        مقداردهی اولیه
        
        Args:
            base_url: آدرس پایه FHIR server
        """
        self.base_url = base_url or "https://fhir.example.com/fhir"
    
    async def create_observation(
        self,
        patient_id: str,
        observation_data: Dict
    ) -> Dict:
        """
        ایجاد Observation در FHIR
        
        Args:
            patient_id: شناسه بیمار
            observation_data: داده‌های observation
        
        Returns:
            FHIR Observation resource
        """
        observation = {
            "resourceType": "Observation",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": observation_data.get("loinc_code", "85354-9"),
                    "display": observation_data.get("display_name", "Observation")
                }]
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": observation_data.get(
                "timestamp",
                datetime.now().isoformat()
            ),
            "valueQuantity": {
                "value": observation_data.get("value", 0),
                "unit": observation_data.get("unit", ""),
                "system": "http://unitsofmeasure.org",
                "code": observation_data.get("unit_code", "")
            }
        }
        
        return observation
    
    async def send_observation(
        self,
        observation: Dict,
        fhir_server_url: Optional[str] = None
    ) -> bool:
        """
        ارسال Observation به FHIR server
        
        Args:
            observation: FHIR Observation resource
            fhir_server_url: آدرس FHIR server (اختیاری)
        
        Returns:
            True در صورت موفقیت
        """
        url = fhir_server_url or f"{self.base_url}/Observation"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=observation,
                    headers={
                        "Content-Type": "application/fhir+json",
                        "Accept": "application/fhir+json"
                    },
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    logger.info("Observation sent to FHIR server")
                    return True
                else:
                    logger.error(f"FHIR server error: {response.status_code}")
                    return False
        
        except Exception as e:
            logger.error(f"Error sending to FHIR server: {e}")
            return False
    
    async def get_patient_observations(
        self,
        patient_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        دریافت Observations بیمار
        
        Args:
            patient_id: شناسه بیمار
            start_date: تاریخ شروع (اختیاری)
            end_date: تاریخ پایان (اختیاری)
        
        Returns:
            لیست Observations
        """
        url = f"{self.base_url}/Observation"
        params = {
            "subject": f"Patient/{patient_id}"
        }
        
        if start_date:
            params["date"] = f"ge{start_date.isoformat()}"
        if end_date:
            params["date"] = f"le{end_date.isoformat()}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    headers={"Accept": "application/fhir+json"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    bundle = response.json()
                    return bundle.get("entry", [])
                
                return []
        
        except Exception as e:
            logger.error(f"Error getting observations: {e}")
            return []
    
    def convert_ms_data_to_fhir(self, ms_data: Dict) -> Dict:
        """
        تبدیل داده MS به FHIR
        
        Args:
            ms_data: داده MS (EEG, biomarker, etc.)
        
        Returns:
            FHIR Observation
        """
        # Map انواع داده MS به LOINC codes
        loinc_mapping = {
            "eeg": "34551-5",  # EEG
            "heart_rate": "8867-4",  # Heart rate
            "blood_pressure": "85354-9",  # Blood pressure
            "temperature": "8310-5",  # Body temperature
        }
        
        data_type = ms_data.get("type", "unknown")
        loinc_code = loinc_mapping.get(data_type, "34551-5")
        
        observation = {
            "resourceType": "Observation",
            "status": "final",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": loinc_code,
                    "display": data_type
                }]
            },
            "subject": {
                "reference": f"Patient/{ms_data.get('patient_id', 'unknown')}"
            },
            "effectiveDateTime": ms_data.get(
                "timestamp",
                datetime.now().isoformat()
            ),
            "valueQuantity": {
                "value": ms_data.get("value", 0),
                "unit": ms_data.get("unit", ""),
                "system": "http://unitsofmeasure.org"
            }
        }
        
        return observation

