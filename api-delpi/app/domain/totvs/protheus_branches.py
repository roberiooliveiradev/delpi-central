"""Filiais Protheus — escopo canônico de consulta (all | 01 | 02)."""

from __future__ import annotations

# Wire OpenAPI / HTTP (EN). Labels PT-BR em openapi_param_locale.json.
BRANCH_SCOPE_ALL = "all"
PROTHEUS_BRANCH_CODES: tuple[str, ...] = ("01", "02")
BRANCH_SCOPE_VALUES: tuple[str, ...] = (BRANCH_SCOPE_ALL, *PROTHEUS_BRANCH_CODES)

# Short site labels (UF) — canonical 01→SC / 02→ES (see padroes-totvs/filiais.md).
PROTHEUS_BRANCH_SHORT_LABELS: dict[str, str] = {
    "01": "SC",
    "02": "ES",
}

# Alias histórico (PT no wire) — normaliza para ``all``.
BRANCH_SCOPE_TODAS = BRANCH_SCOPE_ALL
_BRANCH_SCOPE_ALIASES: dict[str, str] = {
    "all": BRANCH_SCOPE_ALL,
    "todas": BRANCH_SCOPE_ALL,
    "todos": BRANCH_SCOPE_ALL,
    "Todas": BRANCH_SCOPE_ALL,
    "Todos": BRANCH_SCOPE_ALL,
}

# Alias histórico — só códigos de filial (detalhe / chave composta).
BRANCH_CODE_VALUES = PROTHEUS_BRANCH_CODES


def is_all_branches(scope: str) -> bool:
    return str(scope or "").strip().lower() in {"", "all", "todas", "todos"}


def optional_concrete_branch(raw: str | None) -> str | None:
    """None / all / aliases → ``None`` (consolidado); ``01``/``02`` → código.

    Usar em filtros SQL e em use cases que tratam omitido como todas as filiais.
    """
    if raw is None or is_all_branches(str(raw)):
        return None
    return normalize_branch_code(raw)


def normalize_optional_branch_codes(
    raw: list[str] | tuple[str, ...] | str | None,
) -> tuple[str, ...]:
    """Optional multi-branch wire → concrete codes (deterministic order).

    Semantics:
    - omit / empty / ``all`` (and PT aliases) alone → ``()`` (legacy consolidated)
    - ``01`` and/or ``02`` (repeatable) → deduped tuple ordered by
      ``PROTHEUS_BRANCH_CODES``
    - ``all`` mixed with a concrete code → ``ValueError`` (fail-closed)
    - any other code → ``ValueError``
    """
    if raw is None:
        items: list[str] = []
    elif isinstance(raw, str):
        items = [raw]
    else:
        items = list(raw)

    has_all = False
    seen: set[str] = set()
    for item in items:
        text = str(item or "").strip()
        if not text:
            continue
        if is_all_branches(text):
            has_all = True
            continue
        seen.add(normalize_branch_code(text))

    if has_all and seen:
        raise ValueError(
            "branch ambígua: não misture all com filial concreta (01/02)."
        )
    if has_all or not seen:
        return ()
    return tuple(code for code in PROTHEUS_BRANCH_CODES if code in seen)


def normalize_branch_scope(raw: str | None) -> str:
    """Retorna ``all`` | ``01`` | ``02``. Vazio/None/aliases PT → all."""
    normalized = str(raw or "").strip()
    if not normalized:
        return BRANCH_SCOPE_ALL
    if normalized in PROTHEUS_BRANCH_CODES:
        return normalized
    alias = _BRANCH_SCOPE_ALIASES.get(normalized) or _BRANCH_SCOPE_ALIASES.get(
        normalized.lower()
    )
    if alias:
        return alias
    raise ValueError("branch inválida. Use all, 01 ou 02.")


def normalize_branch_code(raw: str | None) -> str:
    """Exige filial concreta 01 ou 02 (sem all)."""
    normalized = str(raw or "").strip()
    if normalized not in PROTHEUS_BRANCH_CODES:
        raise ValueError("branch inválida. Use 01 ou 02.")
    return normalized


def branch_short_label(raw: str | None) -> str:
    """UF curta da filial (SC/ES). Código desconhecido → string vazia após normalize falhar.

    Preferir sobre hardcode ``\"SC\"``/``\"ES\"`` em use cases e responses.
    """
    code = normalize_branch_code(raw)
    return PROTHEUS_BRANCH_SHORT_LABELS[code]


def branch_filter_sql(column: str, scope: str) -> tuple[str, list]:
    """all → sem predicado; 01/02 → ``column = ?``.

    Retorno: (clause, params). Clause vazia = não filtrar por filial.
    """
    resolved = normalize_branch_scope(scope)
    if is_all_branches(resolved):
        return "", []
    return f"{column} = ?", [resolved]


def append_branch_filter(
    clauses: list[str],
    params: list,
    column: str,
    scope: str,
) -> None:
    clause, branch_params = branch_filter_sql(column, scope)
    if clause:
        clauses.append(clause)
        params.extend(branch_params)
