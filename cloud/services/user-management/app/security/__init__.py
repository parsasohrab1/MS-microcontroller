"""
Security Module
ماژول امنیتی User Management Service
"""

from .oauth2 import (
    OAuth2Provider,
    Token,
    TokenData,
    OIDCUserInfo,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    get_oauth2_provider
)
from .rbac import (
    Role,
    Permission,
    RBACManager,
    require_role,
    require_permission,
    check_patient_access,
    check_research_data_access
)
from .audit_logging import (
    AuditEventType,
    AuditLog,
    AuditLogger,
    get_audit_logger
)
from .data_anonymization import (
    AnonymizationMethod,
    DataAnonymizer,
    get_data_anonymizer
)
from .penetration_testing import (
    TestType,
    TestResult,
    PenetrationTester,
    run_penetration_test
)

__all__ = [
    # OAuth2
    "OAuth2Provider",
    "Token",
    "TokenData",
    "OIDCUserInfo",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "get_current_user",
    "get_oauth2_provider",
    # RBAC
    "Role",
    "Permission",
    "RBACManager",
    "require_role",
    "require_permission",
    "check_patient_access",
    "check_research_data_access",
    # Audit Logging
    "AuditEventType",
    "AuditLog",
    "AuditLogger",
    "get_audit_logger",
    # Data Anonymization
    "AnonymizationMethod",
    "DataAnonymizer",
    "get_data_anonymizer",
    # Penetration Testing
    "TestType",
    "TestResult",
    "PenetrationTester",
    "run_penetration_test"
]

