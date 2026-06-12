#!/usr/bin/env python3
"""Bootstrap de filiais a partir de cadastro JSON (schema 1.1) ou labels legados.

Não é migration seed — script operacional pós-V011 (Playbook 18 S1).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tm_app.core.catalogs import FILIAIS  # noqa: E402
from tm_app.infrastructure.persistence.repositories.filial_repository import (  # noqa: E402
    FilialRepository,
)


def _default_label(codigo: str) -> str:
    return FILIAIS.get(codigo, f"Filial {codigo}")


def collect_codigos(payload: dict) -> set[str]:
    codigos: set[str] = set()
    for row in payload.get("processos") or []:
        if isinstance(row, dict) and row.get("filial_id"):
            codigos.add(str(row["filial_id"]).strip())
    for row in payload.get("setor_filiais") or []:
        if isinstance(row, dict) and row.get("filial_id"):
            codigos.add(str(row["filial_id"]).strip())
    for row in payload.get("filiais") or []:
        if isinstance(row, dict) and row.get("codigo_filial"):
            codigos.add(str(row["codigo_filial"]).strip())
    return {c for c in codigos if c}


def bootstrap_from_payload(payload: dict, *, dry_run: bool = False) -> list[dict]:
    labels: dict[str, str] = dict(FILIAIS)
    for row in payload.get("filiais") or []:
        if not isinstance(row, dict):
            continue
        codigo = str(row.get("codigo_filial") or row.get("id") or "").strip()
        nome = str(row.get("nome_filial") or row.get("label") or "").strip()
        if codigo and nome:
            labels[codigo] = nome

    codigos = collect_codigos(payload)
    if not codigos:
        codigos = set(labels.keys())

    results: list[dict] = []
    repo = None if dry_run else FilialRepository()
    for codigo in sorted(codigos):
        nome = labels.get(codigo, _default_label(codigo))
        if dry_run:
            results.append({"codigo_filial": codigo, "nome_filial": nome, "action": "upsert"})
            continue
        assert repo is not None
        row = repo.upsert_bootstrap(codigo, nome)
        results.append(dict(row))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap filiais a partir de cadastro JSON.")
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Arquivo JSON exportado (schema 1.1+) ou cadastro com filiais.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Somente listar upserts.")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.is_file():
        print(f"Arquivo não encontrado: {path}", file=sys.stderr)
        return 1

    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = bootstrap_from_payload(payload, dry_run=args.dry_run)
    print(json.dumps({"total": len(rows), "items": rows}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
