from __future__ import annotations

from flask import Flask, g, jsonify, request

from app.application.ports.platform_access_port import (
    AuthenticationError,
    AuthorityUnavailableError,
)


PUBLIC_PATHS = frozenset({"/health"})


def register_auth_middleware(app: Flask, *, logger) -> None:
    @app.before_request
    def enforce_platform_access():
        path = request.path or "/"
        if path in PUBLIC_PATHS or path.rstrip("/") in PUBLIC_PATHS:
            g.platform_access = None
            return None

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.info("authentication_failed reason=missing_authorization")
            return (
                jsonify({"detail": "Unauthorized", "code": "unauthenticated"}),
                401,
            )
        if not auth_header.startswith("Bearer "):
            logger.info("authentication_failed reason=malformed_bearer")
            return (
                jsonify({"detail": "Unauthorized", "code": "unauthenticated"}),
                401,
            )

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            logger.info("authentication_failed reason=empty_bearer")
            return (
                jsonify({"detail": "Unauthorized", "code": "unauthenticated"}),
                401,
            )

        provider = app.config.get("PLATFORM_ACCESS_PROVIDER")
        if provider is None:
            logger.warning("authority_unavailable reason=provider_not_configured")
            return (
                jsonify(
                    {
                        "detail": "Authorization service unavailable",
                        "code": "authority_unavailable",
                    }
                ),
                503,
            )

        try:
            context = provider.resolve(token)
        except AuthenticationError:
            logger.info("authentication_failed reason=token_or_core_auth")
            return (
                jsonify({"detail": "Unauthorized", "code": "unauthenticated"}),
                401,
            )
        except AuthorityUnavailableError:
            logger.warning("authority_unavailable reason=core_context")
            return (
                jsonify(
                    {
                        "detail": "Authorization service unavailable",
                        "code": "authority_unavailable",
                    }
                ),
                503,
            )

        g.platform_access = context
        return None
