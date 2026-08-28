from __future__ import annotations


def product_code_matches_prefixes(product_code: str | None, prefixes: list[str]) -> bool:
    """True se o código (após trim) começa com algum prefixo declarado."""
    code = (product_code or "").strip()
    if not code or not prefixes:
        return False
    return any(code.startswith(prefix) for prefix in prefixes if prefix)


def product_code_excluded_by_prefixes(
    product_code: str | None, excluded_prefixes: list[str]
) -> bool:
    """True se o código deve ser omitido (começa com algum prefixo de exclusão)."""
    return product_code_matches_prefixes(product_code, excluded_prefixes)
