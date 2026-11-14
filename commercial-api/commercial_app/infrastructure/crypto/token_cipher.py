"""Recoverable token cipher for satisfaction invite links (Fernet)."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


class TokenCipher:
    def __init__(self, key: str):
        if not key or not str(key).strip():
            raise ValueError(
                "COMMERCIAL_SATISFACTION_TOKEN_KEY ausente ou inválida."
            )
        self._fernet = Fernet(str(key).strip().encode("utf-8"))

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError(
                "Não foi possível ler o token cifrado."
            ) from exc
