"""Gera XLSX sanitizado no layout real MyWEG NF Emitidas."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from openpyxl import Workbook

from production_control_app.jobs.myweg_invoice_observations_publisher import (
    EXPECTED_HEADERS,
)
from tests.fixtures.myweg_invoices.sample_reference import (
    build_empty_manifest,
    build_sample_2026_11_05_records,
    build_validated_manifest,
)


def write_invoice_xlsx(path: Path, records: Sequence[dict[str, Any]]) -> str:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(list(EXPECTED_HEADERS))
    for row in records:
        sheet.append(
            [
                row["invoice_number"],
                row["invoice_series"],
                row["material_weg"],
                row.get("material_description") or "",
                row["quantity_original"],
                row["source_unit"],
                row["departure_date"],
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def materialize_sample_collection(
    root: Path,
    *,
    collection_id: str = "col-20261105-sample",
    document_date: str = "2026-11-05",
) -> Path:
    """Cria pasta histórica sanitizada com manifesto + XLSX."""
    directory = (
        root
        / "filial-02"
        / "empresa-1009"
        / "centro-1106"
        / "fornecedor-50471"
        / f"data-documento={document_date}"
        / collection_id
    )
    directory.mkdir(parents=True, exist_ok=True)
    records = build_sample_2026_11_05_records()
    xlsx_name = f"EXPORT_{collection_id}.xlsx"
    sha256 = write_invoice_xlsx(directory / xlsx_name, records)
    manifesto = build_validated_manifest(
        collection_id=collection_id,
        document_date=document_date,
        xlsx_name=xlsx_name,
        sha256=sha256,
        record_count=len(records),
    )
    (directory / "manifesto.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return directory


def materialize_empty_collection(
    root: Path,
    *,
    collection_id: str = "col-20261101-empty",
) -> Path:
    directory = (
        root
        / "filial-02"
        / "empresa-1009"
        / "centro-1106"
        / "fornecedor-50471"
        / "data-documento=2026-11-01"
        / collection_id
    )
    directory.mkdir(parents=True, exist_ok=True)
    manifesto = build_empty_manifest(collection_id=collection_id)
    (directory / "manifesto.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return directory
