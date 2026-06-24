from __future__ import annotations

VALID_PAC_BRANCH_CODES = frozenset({"01", "02"})


def normalize_branch_code(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) == 1 and normalized.isdigit():
        return normalized.zfill(2)
    return normalized


def validate_branch_code(value: str | None, *, required: bool = False) -> str | None:
    normalized = normalize_branch_code(value)
    if normalized is None:
        if required:
            raise ValueError("branch_code é obrigatório (use 01 ou 02).")
        return None
    if normalized not in VALID_PAC_BRANCH_CODES:
        raise ValueError("branch_code inválido. Valores aceitos: 01, 02.")
    return normalized


def build_recurrence_key(
    *,
    branch_code: str | None,
    product_code: str | None,
    failure_mode: str | None,
    explicit: str | None = None,
) -> str | None:
    if explicit and explicit.strip():
        return explicit.strip()
    parts: list[str] = []
    if branch_code:
        parts.append(f"filial:{branch_code}")
    if product_code:
        parts.append(f"produto:{product_code}")
    if failure_mode:
        parts.append(f"falha:{failure_mode.strip()}")
    return "|".join(parts) if parts else None
