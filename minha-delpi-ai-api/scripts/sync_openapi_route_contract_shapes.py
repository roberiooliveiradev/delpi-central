#!/usr/bin/env python3
"""Sincroniza operationId → entity/shape do api-delpi para o chat."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "api-delpi"
    / "app"
    / "interface"
    / "http"
    / "route_contract_registry.py"
)
DEFAULT_TARGET = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "content"
    / "pt-BR"
    / "assistant"
    / "openapi_operation_contracts.json"
)


def _load_contracts_from_api_delpi() -> dict[str, dict[str, str]]:
    api_delpi_root = Path(__file__).resolve().parents[2] / "api-delpi"

    if str(api_delpi_root) not in sys.path:
        sys.path.insert(0, str(api_delpi_root))

    from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

    return {
        operation_id: {"entity": contract.entity, "shape": contract.shape}
        for operation_id, contract in ROUTE_CONTRACTS.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--check", action="store_true", help="Falha se o arquivo estiver desatualizado.")
    args = parser.parse_args()

    generated = _load_contracts_from_api_delpi()
    current: dict[str, dict[str, str]] = {}

    if args.target.is_file():
        payload = json.loads(args.target.read_text(encoding="utf-8"))

        if isinstance(payload, dict):
            current = {
                str(key): value
                for key, value in payload.items()
                if isinstance(value, dict)
            }

    if args.check:
        if current != generated:
            print(
                json.dumps(
                    {
                        "error": "openapi_operation_contracts.json desatualizado",
                        "currentCount": len(current),
                        "generatedCount": len(generated),
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )

            return 1

        print(json.dumps({"ok": True, "contracts": len(current)}, ensure_ascii=False))

        return 0

    args.target.parent.mkdir(parents=True, exist_ok=True)
    args.target.write_text(
        json.dumps(generated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"target": str(args.target), "contracts": len(generated)}, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
