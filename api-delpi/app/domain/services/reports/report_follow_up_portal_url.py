"""URLs do portal para deep links de relatórios (e-mail → MFE)."""

from __future__ import annotations

from urllib.parse import quote

FOLLOW_UP_PATH_PREFIX = "/apps/reports/acompanhamentos"


def build_follow_up_portal_url(
    public_base_url: str | None,
    definition_id: str,
) -> str | None:
    """Monta URL absoluta da tela operacional de acompanhamentos.

    Retorna ``None`` se a base pública ou o id estiverem vazios.
    """
    base = str(public_base_url or "").strip().rstrip("/")
    def_id = str(definition_id or "").strip()
    if not base or not def_id:
        return None
    return f"{base}{FOLLOW_UP_PATH_PREFIX}/{quote(def_id, safe='')}"
