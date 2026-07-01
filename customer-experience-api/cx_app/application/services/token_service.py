from __future__ import annotations

import secrets

# 32 bytes de entropia -> ~43 chars url-safe (>= 256 bits). Não sequencial, não derivado de PII.
_TOKEN_NBYTES = 32


def generate_public_token() -> str:
    return secrets.token_urlsafe(_TOKEN_NBYTES)
