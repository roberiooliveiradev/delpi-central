from __future__ import annotations

import json
from pathlib import Path

from scripts.bootstrap_filiais_from_cadastro import bootstrap_from_payload, collect_codigos

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "cadastro"
    / "transformometro-cadastro-20260612.json"
)


def test_collect_codigos_from_backup_fixture():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    codigos = collect_codigos(payload)
    assert codigos == {"01", "02"}


def test_bootstrap_dry_run_from_backup_fixture():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    rows = bootstrap_from_payload(payload, dry_run=True)
    assert len(rows) == 2
    assert {row["codigo_filial"] for row in rows} == {"01", "02"}
