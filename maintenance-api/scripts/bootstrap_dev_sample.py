#!/usr/bin/env python3
"""Insere reposições de exemplo para desenvolvimento local (relatório preventivo).

Só grava se não existir reposição para o par ferramenta/peça informado.

Exemplo:
  cd maintenance-api
  set -a && source ../infra/.env && set +a
  python scripts/bootstrap_dev_sample.py --filial 01
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maint_app.infrastructure.persistence.plugins.plugin_base_repository import (  # noqa: E402
    PluginBaseRepository,
)


def _motivo_id(repo: PluginBaseRepository) -> int:
    row = repo.fetch_one(
        """
        SELECT motivo_id FROM maintenance.motivos
        WHERE excluido = FALSE
        ORDER BY motivo_id
        LIMIT 1
        """
    )
    if not row:
        raise RuntimeError("Nenhum motivo cadastrado — rode migrations V002.")
    return int(row["motivo_id"])


def bootstrap(
    repo: PluginBaseRepository,
    *,
    filial: str,
    codigo_ferramenta: str,
    codigo_peca: str,
) -> int:
    existing = repo.fetch_one(
        """
        SELECT 1 FROM maintenance.reposicoes
        WHERE filial = %(filial)s
          AND codigo_ferramenta = %(codigo_ferramenta)s
          AND codigo_peca = %(codigo_peca)s
          AND excluido = FALSE
        LIMIT 1
        """,
        {
            "filial": filial,
            "codigo_ferramenta": codigo_ferramenta,
            "codigo_peca": codigo_peca,
        },
    )
    if existing:
        return 0

    motivo_id = _motivo_id(repo)
    now = datetime.now(timezone.utc)
    samples = [
        (now - timedelta(days=120), 130),
        (now - timedelta(days=60), 98),
        (now - timedelta(days=15), 105),
    ]

    for index, (data_reposicao, golpes) in enumerate(samples):
        data_ultima = samples[index - 1][0] if index > 0 else None
        repo.execute(
            """
            INSERT INTO maintenance.reposicoes (
                filial, codigo_ferramenta, codigo_peca,
                data_reposicao, data_ultima_reposicao,
                golpes, motivo_id
            ) VALUES (
                %(filial)s, %(codigo_ferramenta)s, %(codigo_peca)s,
                %(data_reposicao)s, %(data_ultima_reposicao)s,
                %(golpes)s, %(motivo_id)s
            )
            """,
            {
                "filial": filial,
                "codigo_ferramenta": codigo_ferramenta,
                "codigo_peca": codigo_peca,
                "data_reposicao": data_reposicao,
                "data_ultima_reposicao": data_ultima,
                "golpes": golpes,
                "motivo_id": motivo_id,
            },
        )
    return len(samples)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap reposições de dev")
    parser.add_argument("--filial", default="01")
    parser.add_argument("--ferramenta", default="23-001")
    parser.add_argument("--peca", default="P001")
    args = parser.parse_args()

    repo = PluginBaseRepository()
    inserted = bootstrap(
        repo,
        filial=args.filial,
        codigo_ferramenta=args.ferramenta,
        codigo_peca=args.peca,
    )
    if inserted:
        print(f"[OK] Inseridas {inserted} reposições — {args.ferramenta}/{args.peca} filial {args.filial}.")
    else:
        print("[SKIP] Já existem reposições para este par — nada a fazer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
