"""
Data Validators
"""

from typing import Dict, List
from app.models import SensorDataRequest


def validate_sensor_data(request: SensorDataRequest) -> Dict:
    """
    اعتبارسنجی داده سنسور
    
    Args:
        request: درخواست
    
    Returns:
        نتایج اعتبارسنجی
    """
    errors = []
    
    # Validate patient_id
    if not request.patient_id or len(request.patient_id) == 0:
        errors.append("patient_id is required")
    
    # Validate device_id
    if not request.device_id or len(request.device_id) == 0:
        errors.append("device_id is required")
    
    # Validate timestamp
    if not request.timestamp:
        errors.append("timestamp is required")
    
    # Validate EEG data if provided
    if request.eeg_data:
        if not isinstance(request.eeg_data, list):
            errors.append("eeg_data must be a list")
        else:
            # Check structure (should be channels x samples)
            if len(request.eeg_data) == 0:
                errors.append("eeg_data cannot be empty")
            else:
                # Check all channels have same length
                first_length = len(request.eeg_data[0]) if request.eeg_data[0] else 0
                for i, channel in enumerate(request.eeg_data):
                    if not isinstance(channel, list):
                        errors.append(f"eeg_data channel {i} must be a list")
                    elif len(channel) != first_length:
                        errors.append(f"eeg_data channel {i} has inconsistent length")
    
    # Validate biomarker values if provided
    if request.biomarker_values:
        if not isinstance(request.biomarker_values, dict):
            errors.append("biomarker_values must be a dictionary")
        else:
            for key, value in request.biomarker_values.items():
                if not isinstance(value, (int, float)):
                    errors.append(f"biomarker_values[{key}] must be a number")
    
    # Validate physiological params if provided
    if request.physiological_params:
        if not isinstance(request.physiological_params, dict):
            errors.append("physiological_params must be a dictionary")
        else:
            for key, value in request.physiological_params.items():
                if not isinstance(value, (int, float)):
                    errors.append(f"physiological_params[{key}] must be a number")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

