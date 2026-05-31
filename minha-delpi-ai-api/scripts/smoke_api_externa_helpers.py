"""Helpers compartilhados — smokes HTTP devem usar api-externa (api-delpi off no local)."""

from __future__ import annotations

import os

SMOKE_REQUIRE_API_EXTERNA = (
    os.environ.get("SMOKE_REQUIRE_API_EXTERNA", "true").lower() == "true"
)

# Chips sem rota equivalente só em api-externa (ex.: /sales/billing).
CHIPS_SKIP_WHEN_API_EXTERNA_ONLY: dict[str, str] = {
    "Ver vendas": "sem rota de faturamento/vendas em api-externa (use api-delpi em prod)",
}


def action_provider_prefix(action_id: str) -> str:
    value = str(action_id or "").lower()
    if value.startswith("api_externa."):
        return "api_externa"
    if value.startswith("api_delpi."):
        return "api_delpi"
    return ""


def validate_chip_action_id(
    *,
    label: str,
    action_id: str,
    query: str,
) -> tuple[bool, str]:
    """Retorna (ok, mensagem). ok=False indica falha; mensagem vazia se ok."""
    if label in CHIPS_SKIP_WHEN_API_EXTERNA_ONLY and SMOKE_REQUIRE_API_EXTERNA:
        return True, f"SKIP API chip {label}: {CHIPS_SKIP_WHEN_API_EXTERNA_ONLY[label]}"

    if not SMOKE_REQUIRE_API_EXTERNA:
        return True, f"OK API chip {label}: {action_id}"

    prefix = action_provider_prefix(action_id)

    if prefix == "api_externa":
        return True, f"OK API chip {label}: {action_id}"

    if prefix == "api_delpi":
        return (
            False,
            f"FAIL API chip {label!r}: esperado api_externa.*, obteve {action_id!r} "
            f"(query={query!r}; defina CHAT_PREFER_API_EXTERNA_PROVIDER=true)",
        )

    return (
        False,
        f"FAIL API chip {label!r}: actionId={action_id!r} sem prefixo api_externa "
        f"(query={query!r})",
    )
