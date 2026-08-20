from __future__ import annotations


def product_code_matches_prefixes(product_code: str | None, prefixes: list[str]) -> bool:
    """True se o código (após trim) começa com algum prefixo declarado."""
    code = (product_code or "").strip()
    if not code or not prefixes:
        return False
    return any(code.startswith(prefix) for prefix in prefixes if prefix)
