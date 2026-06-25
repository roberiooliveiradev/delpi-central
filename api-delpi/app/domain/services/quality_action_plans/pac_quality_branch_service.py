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


def parse_recurrence_key(recurrence_key: str | None) -> dict[str, str | None]:
    if not recurrence_key or not recurrence_key.strip():
        return {"branch_code": None, "product_code": None, "failure_mode": None}
    branch_code: str | None = None
    product_code: str | None = None
    failure_mode: str | None = None
    for part in recurrence_key.split("|"):
        segment = part.strip()
        if segment.startswith("filial:"):
            branch_code = segment[7:].strip() or None
        elif segment.startswith("produto:"):
            product_code = segment[8:].strip() or None
        elif segment.startswith("falha:"):
            failure_mode = segment[6:].strip() or None
    return {
        "branch_code": branch_code,
        "product_code": product_code,
        "failure_mode": failure_mode,
    }
