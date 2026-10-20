# shared/delpi_auth/__init__.py
"""
DELPI Auth SDK

Módulo compartilhado de autenticação e autorização da plataforma DELPI.

Fornece:

- Validação de JWT (Keycloak)
- Middleware para Flask e FastAPI
- Decorators de autorização
- Policy Engine
- Registro de policies
"""

from .jwt_validator import validate_token

from .authorization import (
    require_auth,
    require_superadmin,
    require_permission,
    require_any_permission,
    require_all_permissions,
)

from .decorators import (
    register_policy,
    policy,
)

from .policy_engine import PolicyEngine
from .policy_registry import PolicyRegistry

from .service_contract import (
    SERVICE_AUTHORIZATION_HEADER,
    build_service_authorization,
    extract_service_authorization,
)
from .service_identity import ServiceIdentity
from .service_errors import ServiceAuthError
from .service_token_validator import ServiceTokenValidator
from .service_token_provider import ClientCredentialsTokenProvider


__all__ = [
    "validate_token",
    "require_auth",
    "require_superadmin",
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
    "register_policy",
    "policy",
    "PolicyEngine",
    "PolicyRegistry",
    "SERVICE_AUTHORIZATION_HEADER",
    "build_service_authorization",
    "extract_service_authorization",
    "ServiceIdentity",
    "ServiceAuthError",
    "ServiceTokenValidator",
    "ClientCredentialsTokenProvider",
]