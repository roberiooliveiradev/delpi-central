#!/usr/bin/env python3
"""Importa dados exportados do Access (CSV) para Postgres maintenance.

Uso típico após exportar do MiniAplicadoresBD:
  TabMotivo.csv, TabStatusPeca.csv, TabReposicoes.csv

Exemplo:
  cd maintenance-api
  set -a && source ../infra/.env && set +a
  python scripts/import_access_csv.py \\
    --motivos ../fixtures/maintenance/access/TabMotivo.csv \\
    --status ../fixtures/maintenance/access/TabStatusPeca.csv \\
    --reposicoes ../fixtures/maintenance/access/TabReposicoes.csv \\
    --filial 01
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maint_app.infrastructure.persistence.plugins.plugin_base_repository import (  # noqa: E402
    PluginBaseRepository,
)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value or not str(value).strip():
        return None
    raw = str(value).strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"Data inválida: {value!r}")


def import_motivos(repo: PluginBaseRepository, path: Path) -> int:
    count = 0
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            descricao = (row.get("Descricao") or row.get("descricao") or "").strip()
            if not descricao:
                continue
            repo.execute(
                """
                INSERT INTO maintenance.motivos (descricao)
                SELECT %(descricao)s
                WHERE NOT EXISTS (
                    SELECT 1 FROM maintenance.motivos m
                    WHERE upper(m.descricao) = upper(%(descricao)s)
                )
                """,
                {"descricao": descricao},
            )
            count += 1
    return count


def import_status(repo: PluginBaseRepository, path: Path) -> int:
    count = 0
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            descricao = (row.get("Descricao") or row.get("descricao") or "").strip()
            operador = (row.get("Operador") or row.get("operador") or "").strip()
            percentual = int(row.get("Percentual") or row.get("percentual") or 0)
            if not descricao or not operador:
                continue
            repo.execute(
                """
                INSERT INTO maintenance.status_peca (descricao, operador, percentual)
                SELECT %(descricao)s, %(operador)s, %(percentual)s
                WHERE NOT EXISTS (
                    SELECT 1 FROM maintenance.status_peca s
                    WHERE upper(s.descricao) = upper(%(descricao)s)
                )
                """,
                {
                    "descricao": descricao,
                    "operador": operador,
                    "percentual": percentual,
                },
            )
            count += 1
    return count


def _resolve_motivo_id(repo: PluginBaseRepository, motivo_raw: str | None) -> str:
    raw = (motivo_raw or "").strip()
    if raw:
        row = repo.fetch_one(
            """
            SELECT motivo_id::text AS motivo_id
            FROM maintenance.motivos
            WHERE motivo_id = %(id)s::uuid
            """,
            {"id": raw},
        )
        if row:
            return str(row["motivo_id"])

    descricao = raw or "DESGASTE"
    if not descricao or descricao.isdigit():
        descricao = "DESGASTE"
    row = repo.fetch_one(
        """
        SELECT motivo_id::text AS motivo_id FROM maintenance.motivos
        WHERE upper(descricao) = upper(%(descricao)s)
        LIMIT 1
        """,
        {"descricao": descricao},
    )
    if row:
        return str(row["motivo_id"])

    row = repo.fetch_one(
        """
        INSERT INTO maintenance.motivos (descricao)
        VALUES (%(descricao)s)
        RETURNING motivo_id::text AS motivo_id
        """,
        {"descricao": descricao},
    )
    return str(row["motivo_id"])


def import_reposicoes(
    repo: PluginBaseRepository,
    path: Path,
    *,
    filial: str,
    dry_run: bool,
) -> int:
    count = 0
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            codigo_ferramenta = (
                row.get("CodigoFerramenta")
                or row.get("codigo_ferramenta")
                or row.get("Ferramenta")
                or ""
            ).strip()
            codigo_peca = (
                row.get("CodigoPeca") or row.get("codigo_peca") or row.get("Peca") or ""
            ).strip()
            golpes_raw = row.get("Golpes") or row.get("golpes") or "0"
            golpes = int(float(golpes_raw))
            if not codigo_ferramenta or not codigo_peca or golpes <= 0:
                continue

            data_reposicao = _parse_datetime(
                row.get("DataReposicao") or row.get("data_reposicao")
            )
            if data_reposicao is None:
                continue

            data_ultima = _parse_datetime(
                row.get("DataUltimaReposicao") or row.get("data_ultima_reposicao")
            )
            motivo_id = _resolve_motivo_id(
                repo,
                row.get("MotivoId") or row.get("motivo_id") or row.get("Motivo"),
            )
            observacao = (row.get("Observacao") or row.get("observacao") or "").strip() or None
            row_filial = (row.get("Filial") or row.get("filial") or filial).strip()[:2]

            if dry_run:
                count += 1
                continue

            repo.execute(
                """
                INSERT INTO maintenance.reposicoes (
                    filial, codigo_ferramenta, codigo_peca,
                    data_reposicao, data_ultima_reposicao,
                    golpes, motivo_id, observacao
                ) VALUES (
                    %(filial)s, %(codigo_ferramenta)s, %(codigo_peca)s,
                    %(data_reposicao)s, %(data_ultima_reposicao)s,
                    %(golpes)s, %(motivo_id)s, %(observacao)s
                )
                """,
                {
                    "filial": row_filial,
                    "codigo_ferramenta": codigo_ferramenta,
                    "codigo_peca": codigo_peca,
                    "data_reposicao": data_reposicao,
                    "data_ultima_reposicao": data_ultima,
                    "golpes": golpes,
                    "motivo_id": motivo_id,
                    "observacao": observacao,
                },
            )
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Access CSV → Postgres maintenance")
    parser.add_argument("--motivos", type=Path, help="TabMotivo.csv")
    parser.add_argument("--status", type=Path, help="TabStatusPeca.csv")
    parser.add_argument("--reposicoes", type=Path, help="TabReposicoes.csv")
    parser.add_argument("--filial", default="01", help="Filial padrão (01|02)")
    parser.add_argument("--dry-run", action="store_true", help="Conta linhas sem gravar")
    args = parser.parse_args()

    if not any([args.motivos, args.status, args.reposicoes]):
        parser.error("Informe ao menos um CSV (--motivos, --status ou --reposicoes).")

    repo = PluginBaseRepository()
    summary: list[str] = []

    if args.motivos:
        summary.append(f"motivos: {import_motivos(repo, args.motivos)} linhas")
    if args.status:
        summary.append(f"status: {import_status(repo, args.status)} linhas")
    if args.reposicoes:
        summary.append(
            f"reposições: {import_reposicoes(repo, args.reposicoes, filial=args.filial, dry_run=args.dry_run)} linhas"
        )

    mode = "dry-run" if args.dry_run else "importado"
    print(f"[OK] {mode}: " + "; ".join(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
