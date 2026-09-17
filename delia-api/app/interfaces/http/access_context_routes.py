from __future__ import annotations

from flask import Blueprint, g, jsonify

access_context_bp = Blueprint("access_context", __name__)


@access_context_bp.get("/access-context")
def get_access_context():
    """C1 bootstrap probe: expose Core-backed platform access only.

    Not a business API. Never returns raw JWT or secrets.
    """
    context = getattr(g, "platform_access", None)
    if context is None:
        return jsonify({"detail": "Unauthorized", "code": "unauthenticated"}), 401
    return jsonify(context.to_public_dict()), 200
