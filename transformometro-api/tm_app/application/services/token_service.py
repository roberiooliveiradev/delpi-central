from __future__ import annotations

import hashlib
import secrets


def generate_public_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(str(raw_token or "").encode("utf-8")).hexdigest()
