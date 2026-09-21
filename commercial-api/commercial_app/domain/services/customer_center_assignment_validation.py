"""Conference of a portfolio center against SA7 assignments. No allowlist."""

from __future__ import annotations


def validate_customer_center_assignment(
    center: str | None,
    known_centers: list[str] | None,
) -> str | None:
    """Return the center to store.

    Empty ``known_centers`` means the store has no SA7 center: only a blank
    center is accepted (pair fallback). A non-empty catalog requires a member.
    """
    chosen = str(center or "").strip()
    known = [str(item or "").strip() for item in (known_centers or []) if str(item or "").strip()]
    if not known:
        if chosen:
            raise ValueError("Centro do cliente não encontrado na amarração.")
        return None
    if not chosen:
        raise ValueError("Esta loja possui centros. Informe o centro do cliente.")
    if chosen not in known:
        raise ValueError("Centro do cliente não encontrado na amarração.")
    return chosen
