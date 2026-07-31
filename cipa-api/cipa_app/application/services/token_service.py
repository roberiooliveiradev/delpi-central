from __future__ import annotations

import secrets


def generate_public_token() -> str:
    return secrets.token_urlsafe(32)
