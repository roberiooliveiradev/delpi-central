#!/usr/bin/env python3
"""Adiciona depends_on: plugin-ui nos serviços MFE federados do Compose."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FEDERATED_PLUGINS = {
    "controle-retrabalhos",
    "dashboard-production",
    "dashboard-commercial",
    "dashboard-engineering",
    "dashboard-financial",
    "dashboard-hr",
    "dashboard-lmps",
    "dashboard-quality",
    "dashboard-supplies",
    "transformometro",
    "quality-action-plans",
    "cadastro-kaizen",
    "maintenance",
    "eficiencia-fabril",
    "minha-delpi-chat",
    "auditoria-5s",
    "inspecoes-entrada",
    "inspecoes-processo",
    "pedidos-venda-abertos",
    "propostas-comerciais",
    "financeiro-centro-custo",
    "strategic-indicators",
    "customer-experience",
    "cultura-delpi",
    "central-agendamento",
    "quality-labels",
    "tv-dashboard",
    "public-hub",
}

COMPOSE_FILES = [
    ROOT / "infra" / "docker-compose.dev.yml",
    ROOT / "infra" / "docker-compose.yml",
]


def patch_dev_compose(text: str) -> str:
    anchor = """x-plugin-ui-federated: &plugin-ui-federated
  <<: *plugin-profile
  depends_on:
    - plugin-ui

"""
    if "x-plugin-ui-federated:" not in text:
        text = text.replace(
            "x-plugin-profile: &plugin-profile\n  profiles:\n    - plugins\n\nservices:",
            "x-plugin-profile: &plugin-profile\n  profiles:\n    - plugins\n\n"
            + anchor
            + "services:",
        )

    for name in sorted(FEDERATED_PLUGINS):
        federated_line = f"  {name}:\n    <<: *plugin-ui-federated\n"
        if federated_line in text:
            continue

        explicit = (
            f"  {name}:\n"
            "    <<: *plugin-profile\n"
            "    depends_on:\n"
            "      - plugin-ui\n"
        )
        if explicit in text:
            text = text.replace(explicit, federated_line)
            continue

        profile_only = f"  {name}:\n    <<: *plugin-profile\n"
        if profile_only in text:
            text = text.replace(profile_only, federated_line, 1)

    return text


def patch_prod_compose(text: str) -> str:
    for name in sorted(FEDERATED_PLUGINS):
        marker = f"  {name}:\n    depends_on:\n      - plugin-ui\n"
        if marker in text:
            continue
        profile_only = f"  {name}:\n    build:"
        replacement = (
            f"  {name}:\n"
            "    depends_on:\n"
            "      - plugin-ui\n"
            "    build:"
        )
        if profile_only in text:
            text = text.replace(profile_only, replacement, 1)
    return text


def main() -> int:
    for path in COMPOSE_FILES:
        original = path.read_text(encoding="utf-8")
        updated = patch_dev_compose(original) if path.name == "docker-compose.dev.yml" else patch_prod_compose(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            print(f"[OK] {path.relative_to(ROOT)}")
        else:
            print(f"[skip] {path.relative_to(ROOT)} (sem alterações)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
