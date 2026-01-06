"""
GraphQL Schema
Schema برای GraphQL API
"""

from typing import List, Optional
from graphene import ObjectType, String, Int, Float, List as GQLList, Field, Schema
from graphene_sqlalchemy import SQLAlchemyObjectType
from datetime import datetime
import graphene


# ============================================================================
# GraphQL Types
# ============================================================================

class PatientType(ObjectType):
    """نوع Patient در GraphQL"""
    id = String()
    name = String()
    email = String()
    patient_id = String()
    created_at = String()
    risk_score = Float()
    last_update = String()


class SensorDataType(ObjectType):
    """نوع Sensor Data در GraphQL"""
    id = String()
    patient_id = String()
    timestamp = String()
    eeg_data = GQLList(Float)
    biomarker_values = GQLList(Float)
    risk_score = Float()


class PredictionType(ObjectType):
    """نوع Prediction در GraphQL"""
    id = String()
    patient_id = String()
    timestamp = String()
    attack_probability = Float()
    attack_severity = Float()
    attack_duration = Float()
    confidence = Float()


class AlertType(ObjectType):
    """نوع Alert در GraphQL"""
    id = String()
    patient_id = String()
    message = String()
    level = String()
    timestamp = String()
    acknowledged = graphene.Boolean()


# ============================================================================
# Query Types
# ============================================================================

class Query(ObjectType):
    """Root Query Type"""
    
    # Patient queries
    patient = Field(PatientType, patient_id=String(required=True))
    patients = GQLList(PatientType, limit=Int(), offset=Int())
    
    # Sensor data queries
    sensor_data = GQLList(
        SensorDataType,
        patient_id=String(required=True),
        start_date=String(),
        end_date=String(),
        limit=Int()
    )
    
    # Prediction queries
    predictions = GQLList(
        PredictionType,
        patient_id=String(required=True),
        start_date=String(),
        end_date=String(),
        limit=Int()
    )
    
    # Alert queries
    alerts = GQLList(
        AlertType,
        patient_id=String(),
        level=String(),
        limit=Int()
    )
    
    def resolve_patient(self, info, patient_id):
        """Resolver برای patient"""
        # TODO: دریافت از database
        from ..services.patient_service import get_patient
        return get_patient(patient_id)
    
    def resolve_patients(self, info, limit=None, offset=None):
        """Resolver برای patients"""
        # TODO: دریافت از database
        from ..services.patient_service import get_patients
        return get_patients(limit=limit, offset=offset)
    
    def resolve_sensor_data(self, info, patient_id, start_date=None, end_date=None, limit=None):
        """Resolver برای sensor data"""
        # TODO: دریافت از database
        from ..services.data_service import get_sensor_data
        return get_sensor_data(
            patient_id=patient_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    
    def resolve_predictions(self, info, patient_id, start_date=None, end_date=None, limit=None):
        """Resolver برای predictions"""
        # TODO: دریافت از database
        from ..services.prediction_service import get_predictions
        return get_predictions(
            patient_id=patient_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    
    def resolve_alerts(self, info, patient_id=None, level=None, limit=None):
        """Resolver برای alerts"""
        # TODO: دریافت از database
        from ..services.alert_service import get_alerts
        return get_alerts(
            patient_id=patient_id,
            level=level,
            limit=limit
        )


# ============================================================================
# Mutation Types
# ============================================================================

class CreatePatientInput(graphene.InputObjectType):
    """Input برای ایجاد patient"""
    name = String(required=True)
    email = String(required=True)
    patient_id = String(required=True)


class CreatePatient(graphene.Mutation):
    """Mutation برای ایجاد patient"""
    
    class Arguments:
        input = CreatePatientInput(required=True)
    
    patient = Field(PatientType)
    
    def mutate(self, info, input):
        # TODO: ایجاد patient
        from ..services.patient_service import create_patient
        patient = create_patient(input)
        return CreatePatient(patient=patient)


class Mutation(ObjectType):
    """Root Mutation Type"""
    create_patient = CreatePatient.Field()


# ============================================================================
# Schema
# ============================================================================

schema = Schema(query=Query, mutation=Mutation)

