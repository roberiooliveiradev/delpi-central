"""Runner operacional da prévia MyWEG Demanda (somente leitura).

Homologação segura no srv-api (container production-control-api):

  # Obter JWT de usuário real (Portal / Keycloak) com as permissões:
  #   production-control.access
  #   production-control.demand.view
  #   production-control.myweg-needs.view
  #   production-control.view.filial-02
  export ACCESS_TOKEN='<jwt-sem-prefixo-Bearer>'

  python -m production_control_app.jobs.myweg_demand_coverage_preview \\
    --branch 02 --warehouse 01

A identidade vem exclusivamente do JWT validado (delpi_auth) + RBAC Core /me.
Não existe ``--user-json`` nem elevação por ``is_superadmin`` informado pelo operador.
O token nunca é impresso. Sem ACCESS_TOKEN a execução live permanece bloqueada.
Não altera GET /demand. Não escreve Protheus/MyWEG.
"""

from __future__ import annotations

import argparse
import json
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prévia interna MyWEG × Demanda (filial 02) — somente leitura. "
            "Requer ACCESS_TOKEN (JWT de usuário)."
        )
    )
    parser.add_argument(
        "--branch",
        default="02",
        help="Filial DELPI (apenas 02 é válida).",
    )
    parser.add_argument(
        "--warehouse",
        default="01",
        help="Armazém SB2 para exclusivos MyWEG (somente 01 nesta integração).",
    )
    parser.add_argument(
        "--token-env",
        default="ACCESS_TOKEN",
        help="Nome da variável de ambiente com o JWT (default: ACCESS_TOKEN).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    # Bloqueia legado de elevação sintética se alguém ainda passar a flag.
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    for arg in raw_argv:
        if arg == "--user-json" or arg.startswith("--user-json="):
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": (
                            "Flag --user-json removida. Use ACCESS_TOKEN com JWT "
                            "de usuário autenticado (delpi_auth + Core /me). "
                            "Elevação sintética (is_superadmin) não é aceita."
                        ),
                        "status": "AUTH_BLOCKED",
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 2

    parser = build_parser()
    args = parser.parse_args(argv)

    from production_control_app.jobs.myweg_demand_coverage_preview.auth import (
        PreviewAuthError,
        authenticate_preview_user,
        release_preview_auth,
    )

    auth_ctx = None
    try:
        user, auth_ctx = authenticate_preview_user(env_var=args.token_env)
    except PreviewAuthError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "required_permissions": [
                        "production-control.access",
                        "production-control.demand.view",
                        "production-control.myweg-needs.view",
                        "production-control.view.filial-02",
                    ],
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2

    try:
        from production_control_app.composition.pc_composer import (
            build_myweg_demand_coverage_preview_service,
        )

        service = build_myweg_demand_coverage_preview_service()
        preview = service.build_preview(
            user, branch=args.branch, warehouse=args.warehouse
        )
    except PermissionError as exc:
        print(
            json.dumps({"ok": False, "error": str(exc), "status": "FORBIDDEN"}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 3
    except Exception as exc:  # noqa: BLE001
        # Sem stack trace / secrets ao operador.
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Falha interna na prévia (detalhes nos logs do serviço).",
                    "error_type": type(exc).__name__,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1
    finally:
        if auth_ctx is not None:
            release_preview_auth(auth_ctx)

    print(json.dumps({"ok": True, "preview": preview}, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
