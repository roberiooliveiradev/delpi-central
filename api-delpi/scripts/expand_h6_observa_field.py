#!/usr/bin/env python3
"""Expande H6_OBSERVA (apontamentos SH6) além do varchar(30) do dicionário Protheus.

Causa: operadores digitam observação > 30 chars; o Protheus grava só os 30 primeiros
(SX3 X3_TAMANHO=30 + coluna física). Histórico já truncado **não** é recuperável.

Este script:
  1) atualiza SX3*.X3_TAMANHO de H6_OBSERVA;
  2) ALTER COLUMN nas tabelas SH6* com H6_OBSERVA;
  3) sp_refreshview em VW_BI_RT_HORAS_IMPRODUTIVAS.

Uso (produção / container api-delpi):
  docker exec delpi-api-delpi python scripts/expand_h6_observa_field.py
  docker exec delpi-api-delpi python scripts/expand_h6_observa_field.py --apply --size 120
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.infrastructure.persistence.totvs.base_repository import BaseRepository  # noqa: E402

DEFAULT_SIZE = 120
VIEW_NAME = "VW_BI_RT_HORAS_IMPRODUTIVAS"
FIELD = "H6_OBSERVA"


class _Repo(BaseRepository):
    def run_dicts(self, sql: str, params: tuple = ()) -> list[dict]:
        with self:
            return self.execute_query(sql, params) or []

    def run_ddl(self, sql: str, params: tuple = ()) -> None:
        with self:
            assert self.cursor is not None
            assert self.connection is not None
            self.cursor.execute(sql, params)
            self.connection.commit()


def _list_sh6_tables(repo: _Repo) -> list[str]:
    rows = repo.run_dicts(
        """
        SELECT TABLE_NAME AS table_name
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE COLUMN_NAME = ?
          AND TABLE_SCHEMA = 'dbo'
          AND TABLE_NAME LIKE 'SH6%'
        ORDER BY TABLE_NAME
        """,
        (FIELD,),
    )
    return [str(r["table_name"]) for r in rows]


def _list_sx3_tables(repo: _Repo) -> list[str]:
    rows = repo.run_dicts(
        """
        SELECT TABLE_NAME AS table_name
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'dbo'
          AND TABLE_TYPE = 'BASE TABLE'
          AND (
            TABLE_NAME = 'SX3'
            OR (
              TABLE_NAME LIKE 'SX3%'
              AND TABLE_NAME NOT LIKE '%[_]%[_]%'
              AND TABLE_NAME NOT LIKE '%LOG%'
              AND LEN(TABLE_NAME) BETWEEN 3 AND 6
            )
          )
        ORDER BY TABLE_NAME
        """
    )
    # Keep only dictionary tables that actually have the field.
    out: list[str] = []
    for name in [str(r["table_name"]) for r in rows]:
        if name.startswith("SX3X"):
            continue
        found = repo.run_dicts(
            f"""
            SELECT TOP 1 1 AS ok
            FROM [{name}] WITH (NOLOCK)
            WHERE RTRIM(X3_CAMPO) = ?
            """,
            (FIELD,),
        )
        if found:
            out.append(name)
    return out


def _column_size(repo: _Repo, table: str) -> int | None:
    rows = repo.run_dicts(
        """
        SELECT CHARACTER_MAXIMUM_LENGTH AS size
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo'
          AND TABLE_NAME = ?
          AND COLUMN_NAME = ?
        """,
        (table, FIELD),
    )
    if not rows or rows[0].get("size") is None:
        return None
    return int(rows[0]["size"])


def _sx3_size(repo: _Repo, table: str) -> float | None:
    rows = repo.run_dicts(
        f"""
        SELECT TOP 1 X3_TAMANHO AS size
        FROM [{table}] WITH (NOLOCK)
        WHERE RTRIM(X3_CAMPO) = ?
        """,
        (FIELD,),
    )
    if not rows or rows[0].get("size") is None:
        return None
    return float(rows[0]["size"])


def _view_obs_size(repo: _Repo) -> int | None:
    rows = repo.run_dicts(
        """
        SELECT CHARACTER_MAXIMUM_LENGTH AS size
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo'
          AND TABLE_NAME = ?
          AND COLUMN_NAME = 'OBSERVACAO'
        """,
        (VIEW_NAME,),
    )
    if not rows or rows[0].get("size") is None:
        return None
    return int(rows[0]["size"])


def plan(repo: _Repo, size: int) -> dict[str, Any]:
    sh6 = []
    for table in _list_sh6_tables(repo):
        current = _column_size(repo, table)
        sh6.append(
            {
                "table": table,
                "current": current,
                "action": "alter" if current is not None and current < size else "skip",
            }
        )

    sx3 = []
    for table in _list_sx3_tables(repo):
        current = _sx3_size(repo, table)
        sx3.append(
            {
                "table": table,
                "current": current,
                "action": "update" if current is not None and current < size else "skip",
            }
        )

    return {
        "field": FIELD,
        "target_size": size,
        "view": VIEW_NAME,
        "view_observacao_current": _view_obs_size(repo),
        "sh6": sh6,
        "sx3": sx3,
        "note": (
            "Registros já gravados com corte em 30 caracteres não são recuperáveis; "
            "a expansão só evita truncamento em novos apontamentos."
        ),
    }


def apply(repo: _Repo, size: int, planned: dict[str, Any]) -> dict[str, Any]:
    done: dict[str, Any] = {"sx3": [], "sh6": [], "view_refresh": False}

    for item in planned["sx3"]:
        if item["action"] != "update":
            continue
        table = item["table"]
        repo.run_ddl(
            f"""
            UPDATE [{table}]
            SET X3_TAMANHO = ?
            WHERE RTRIM(X3_CAMPO) = ?
            """,
            (float(size), FIELD),
        )
        done["sx3"].append({"table": table, "size": size})

    for item in planned["sh6"]:
        if item["action"] != "alter":
            continue
        table = item["table"]
        repo.run_ddl(
            f"""
            ALTER TABLE [{table}]
            ALTER COLUMN [{FIELD}] VARCHAR({int(size)}) NOT NULL
            """
        )
        done["sh6"].append({"table": table, "size": size})

    repo.run_ddl(f"EXEC sp_refreshview N'dbo.{VIEW_NAME}'")
    done["view_refresh"] = True
    done["view_observacao_after"] = _view_obs_size(repo)
    return done


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--size",
        type=int,
        default=DEFAULT_SIZE,
        help=f"Novo tamanho de H6_OBSERVA (default {DEFAULT_SIZE})",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Executa UPDATE SX3 + ALTER COLUMN + refresh da view (sem isso só planeja)",
    )
    args = parser.parse_args()
    if args.size < 31 or args.size > 254:
        print("size deve estar entre 31 e 254", file=sys.stderr)
        return 2

    repo = _Repo()
    planned = plan(repo, args.size)
    print(json.dumps({"plan": planned}, ensure_ascii=False, indent=2))

    if not args.apply:
        print("Dry-run OK. Reexecute com --apply para gravar.", file=sys.stderr)
        return 0

    result = apply(repo, args.size, planned)
    print(json.dumps({"applied": result}, ensure_ascii=False, indent=2))
    after = plan(repo, args.size)
    print(json.dumps({"verify": after}, ensure_ascii=False, indent=2))
    pending = [
        *(x for x in after["sh6"] if x["action"] == "alter"),
        *(x for x in after["sx3"] if x["action"] == "update"),
    ]
    if pending:
        print("Ainda há pendências após apply:", pending, file=sys.stderr)
        return 1
    view_size = after.get("view_observacao_current") or 0
    if view_size < args.size:
        print(
            "AVISO: view OBSERVACAO ainda reporta tamanho "
            f"{view_size}; confira definição da view.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
