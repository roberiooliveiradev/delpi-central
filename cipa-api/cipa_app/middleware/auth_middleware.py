from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware

__all__ = ["jwt_middleware"]

jwt_middleware = _base_jwt_middleware
