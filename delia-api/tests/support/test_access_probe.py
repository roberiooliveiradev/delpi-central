"""Test-only authenticated probe. Never registered by production composition."""

from __future__ import annotations

from flask import Flask, g, jsonify


TEST_PLATFORM_ACCESS_PATH = "/__test__/platform-access"


def register_test_platform_access_probe(app: Flask) -> None:
    """Expose g.platform_access for middleware contract assertions only."""

    @app.get(TEST_PLATFORM_ACCESS_PATH)
    def _test_platform_access_probe():
        context = getattr(g, "platform_access", None)
        if context is None:
            return jsonify({"detail": "Unauthorized", "code": "unauthenticated"}), 401
        return (
            jsonify(
                {
                    "user_id": context.user_id,
                    "roles": list(context.roles),
                    "groups": list(context.groups),
                    "effective_permissions": list(context.effective_permissions),
                    "is_superadmin": context.is_superadmin,
                    "source": context.source,
                }
            ),
            200,
        )
