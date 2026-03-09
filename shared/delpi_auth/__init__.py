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

# JWT
from .jwt_validator import validate_token

# Authorization decorators
from .authorization import (
    require_auth,
    require_superadmin,
    require_permission,
)

# Policies
from .decorators import (
    register_policy,
    policy,
)

# Policy Engine
from .policy_engine import PolicyEngine
from .policy_registry import PolicyRegistry


__all__ = [

    # JWT
    "validate_token",

    # Authorization
    "require_auth",
    "require_superadmin",
    "require_permission",

    # Policies
    "register_policy",
    "policy",

    # Engine
    "PolicyEngine",
    "PolicyRegistry",
]