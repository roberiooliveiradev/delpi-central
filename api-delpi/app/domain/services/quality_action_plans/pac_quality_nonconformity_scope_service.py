from __future__ import annotations

VALID_NONCONFORMITY_SCOPES = frozenset({"internal", "external"})
DEFAULT_NONCONFORMITY_SCOPE = "external"


def validate_nonconformity_scope(
    value: str | None,
    *,
    required: bool = True,
) -> str:
    if value is None or not str(value).strip():
        if required:
            raise ValueError("nonconformity_scope é obrigatório (internal ou external).")
        return DEFAULT_NONCONFORMITY_SCOPE

    normalized = str(value).strip().lower()
    if normalized not in VALID_NONCONFORMITY_SCOPES:
        raise ValueError("nonconformity_scope inválido. Use internal ou external.")
    return normalized
