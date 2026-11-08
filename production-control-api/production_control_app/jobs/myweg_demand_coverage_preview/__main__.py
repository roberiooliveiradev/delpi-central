"""Runner operacional da prévia MyWEG Demanda (somente leitura).

Uso típico no srv-api (dentro do container production-control-api), com JWT
de operador que já possui demand.view + myweg-needs.view + filial-02:

  python -m production_control_app.jobs.myweg_demand_coverage_preview \\
    --user-json '{"is_superadmin":true}'

Não altera GET /demand. Não escreve Protheus/MyWEG. Saída agregada em JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from types import SimpleNamespace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prévia interna MyWEG × Demanda (filial 02) — somente leitura."
    )
    parser.add_argument(
        "--branch",
        default="02",
        help="Filial DELPI (apenas 02 é válida).",
    )
    parser.add_argument(
        "--warehouse",
        default="01",
        help="Armazém SB2 para exclusivos MyWEG.",
    )
    parser.add_argument(
        "--user-json",
        default='{"is_superadmin":false,"permissions":[]}',
        help="Usuário sintético JSON (permissions / is_superadmin).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    raw_user = json.loads(args.user_json)
    user = SimpleNamespace(
        is_superadmin=bool(raw_user.get("is_superadmin")),
        permissions=set(raw_user.get("permissions") or []),
    )
    from production_control_app.composition.pc_composer import (
        build_myweg_demand_coverage_preview_service,
    )

    service = build_myweg_demand_coverage_preview_service()
    try:
        preview = service.build_preview(
            user, branch=args.branch, warehouse=args.warehouse
        )
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    # Remove amostra de itens detalhados demais se o operador quiser só resumo:
    # mantém items_sample curto já limitado pelo serviço.
    print(json.dumps({"ok": True, "preview": preview}, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
