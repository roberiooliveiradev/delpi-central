#!/usr/bin/env python3
"""Gate anti-YYYYMMDD em payloads de calendário (resposta HTTP).

Varre fixtures JSON de testes e falha se chaves conhecidas de data de calendário
contiverem ``YYYYMMDD`` cru (``^\\d{8}$``), exceto allowlist.

Uso:
  python scripts/audit_response_calendar_dates.py --check
  python scripts/audit_response_calendar_dates.py --write   # regenera inventário
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

API_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = API_ROOT / "app" / "content" / "response_calendar_date_inventory.json"
FIXTURE_ROOTS = (
    API_ROOT / "tests" / "fixtures",
    API_ROOT / "tests" / "support",
)

YMD_RE = re.compile(r"^\d{8}$")

# Chaves de calendário (sem hora) que devem ser ISO na resposta.
DATE_KEYS = frozenset(
    {
        "start_date",
        "end_date",
        "date_start",
        "date_end",
        "date_end_exclusive",
        "end_date_exclusive",
        "reference_date",
        "issue_date",
        "loss_date",
        "data_limite",
        "homolog_date",
        "limit_date",
        "next_start_date",
        "panel_start_date",
        "closing_base_date",
        "official_closure_date",
        "last_revision_date",
        "last_sale_date",
        "first_billing_date",
        "last_purchase_date",
        "proposal_date",
        "data_emissao",
        "data_proposta",
        "data_inicio",
        "data_fim",
        "start",
        "end",
        "data",
    }
)

# Paths relativos (posix) cujo conteúdo YMD é permitido (SQL interno, input, exempt).
DEFAULT_ALLOWLIST: list[str] = [
    # Exemplo: "tests/fixtures/internal_sql_params.json::period.start"
]


def _iter_json_files() -> list[Path]:
    files: list[Path] = []
    for root in FIXTURE_ROOTS:
        if not root.is_dir():
            continue
        files.extend(sorted(root.rglob("*.json")))
    return files


def _walk(
    node: Any,
    *,
    path: str,
    hits: list[dict[str, str]],
) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}" if path else str(key)
            key_l = str(key)
            if key_l in DATE_KEYS and isinstance(value, str) and YMD_RE.match(value.strip()):
                hits.append({"path": child, "value": value.strip(), "key": key_l})
            _walk(value, path=child, hits=hits)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _walk(item, path=f"{path}[{index}]", hits=hits)


def scan() -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for file_path in _iter_json_files():
        rel = file_path.relative_to(API_ROOT).as_posix()
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        file_hits: list[dict[str, str]] = []
        _walk(payload, path="", hits=file_hits)
        for hit in file_hits:
            hits.append(
                {
                    "file": rel,
                    "path": f"{rel}::{hit['path']}",
                    "key": hit["key"],
                    "value": hit["value"],
                }
            )
    return hits


def load_inventory() -> dict[str, Any]:
    if not INVENTORY_PATH.is_file():
        return {
            "contract": "YYYY-MM-DD",
            "dataVersion": "2026-07",
            "allowlist": DEFAULT_ALLOWLIST,
            "notes": (
                "Datas de calendário na resposta HTTP devem ser ISO. "
                "YYYYMMDD só em allowlist (SQL/params internos)."
            ),
        }
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def write_inventory(hits: list[dict[str, str]]) -> None:
    inventory = load_inventory()
    inventory["dataVersion"] = "2026-07"
    inventory["contract"] = "YYYY-MM-DD"
    inventory["allowlist"] = sorted(
        set(inventory.get("allowlist") or []) | set(DEFAULT_ALLOWLIST)
    )
    inventory["lastScanYmdHits"] = [
        {"path": h["path"], "value": h["value"]} for h in hits
    ]
    INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY_PATH.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def check() -> int:
    inventory = load_inventory()
    allow = set(inventory.get("allowlist") or [])
    hits = scan()
    violations = [h for h in hits if h["path"] not in allow]
    if violations:
        print(
            f"FAIL: {len(violations)} data(s) de calendário em YYYYMMDD "
            f"(contrato ISO YYYY-MM-DD):",
            file=sys.stderr,
        )
        for hit in violations[:50]:
            print(f"  - {hit['path']} = {hit['value']}", file=sys.stderr)
        if len(violations) > 50:
            print(f"  … +{len(violations) - 50} mais", file=sys.stderr)
        return 1
    print(
        f"OK: nenhum YYYYMMDD em chaves de calendário "
        f"({len(hits)} hit(s) allowlisted)."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if not args.check and not args.write:
        parser.error("informe --check e/ou --write")

    hits = scan()
    if args.write:
        write_inventory(hits)
        print(f"Inventário escrito: {INVENTORY_PATH} ({len(hits)} hit(s) YMD).")
    if args.check:
        return check()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
