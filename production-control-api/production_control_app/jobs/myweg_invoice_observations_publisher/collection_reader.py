"""Leitura segura de pastas históricas MyWEG NF Emitidas (somente leitura)."""

from __future__ import annotations

import hashlib
import json
import logging
import time
import zipfile
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from openpyxl import load_workbook

from production_control_app.domain.myweg_invoice_observations_contract import (
    ALLOWED_BRANCH,
    MANIFEST_STATUS_EMPTY_SAP,
    MANIFEST_STATUS_VALIDATED,
    MYWEG_COMPANY_CODE,
    MYWEG_SUPPLIER_CODE,
    MYWEG_WORK_CENTER,
    OBSERVATION_STATUS_EMPTY_SIGNALED_BY_SAP,
    OBSERVATION_STATUS_WITH_RECORDS,
    decimal_to_canonical_str,
    manifest_status_to_observation_status,
    quantity_to_un,
)
from production_control_app.jobs.myweg_invoice_observations_publisher import (
    EXPECTED_HEADERS,
)

logger = logging.getLogger(__name__)

_SAO_PAULO = ZoneInfo("America/Sao_Paulo")
_MAX_MANIFEST_BYTES = 256 * 1024
_MAX_XLSX_BYTES = 25 * 1024 * 1024
_MAX_UNCOMPRESSED_ZIP_BYTES = 80 * 1024 * 1024
_MAX_ROWS = 50_000
_MAX_PROCESS_SECONDS = 60.0
_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class InvoiceCollectionArtifacts:
    collection_id: str
    directory: Path
    document_date: date
    observation_status: str
    observed_at: datetime | None
    source_prepared_at: datetime
    source_sha256: str | None
    manifesto: dict[str, Any]
    records: list[dict[str, Any]]
    xlsx_name: str | None


class InvoiceCollectionReadError(ValueError):
    """Falha de leitura/validação — NÃO equivale a zero notas."""


class InvoiceCollectionIncompleteError(InvoiceCollectionReadError):
    """Pasta incompleta, instável ou ausente — NÃO é empty_signaled_by_sap."""


def list_invoice_collection_dirs(root: Path) -> list[Path]:
    """Lista pastas de coleta com manifesto.json sob a raiz histórica (somente leitura)."""
    root = root.expanduser().resolve(strict=False)
    if not root.is_dir():
        return []
    found: list[Path] = []
    for manifesto in root.rglob("manifesto.json"):
        parent = manifesto.parent
        if not parent.is_dir():
            continue
        # Esperado: .../data-documento=YYYY-MM-DD/<collection_id>/manifesto.json
        # Aceita também fixture flat (path_identity_soft).
        found.append(parent)
    found.sort(key=lambda path: (path.parent.name, path.name))
    return found


def resolve_collection_dir(
    root: Path,
    *,
    collection_id: str | None = None,
    directory: Path | None = None,
) -> Path:
    if directory is not None:
        return directory.expanduser().resolve(strict=False)
    if not collection_id:
        raise InvoiceCollectionIncompleteError(
            "Informe --collection-id ou --directory."
        )
    root = root.expanduser().resolve(strict=False)
    if not root.is_dir():
        raise InvoiceCollectionIncompleteError(f"Raiz inexistente: {root}")
    matches = list(root.rglob(collection_id))
    dirs = [path for path in matches if path.is_dir() and path.name == collection_id]
    if not dirs:
        raise InvoiceCollectionIncompleteError(
            f"collection_id não encontrado sob {root}: {collection_id}"
        )
    if len(dirs) > 1:
        raise InvoiceCollectionIncompleteError(
            f"collection_id ambíguo ({len(dirs)} pastas): {collection_id}"
        )
    return dirs[0]


def load_invoice_collection(
    directory: Path,
    *,
    stability_wait_seconds: float = 0.75,
    expected_collection_id: str | None = None,
) -> InvoiceCollectionArtifacts:
    started = time.monotonic()
    directory = _assert_safe_dir(directory)
    collection_id = directory.name.strip()
    if not collection_id:
        raise InvoiceCollectionIncompleteError("collection_id vazio.")
    if expected_collection_id and expected_collection_id.strip() != collection_id:
        raise InvoiceCollectionReadError(
            f"collection_id da pasta ({collection_id}) ≠ "
            f"esperado ({expected_collection_id})."
        )

    lock_present = (directory / ".lock").exists() or (directory / "etl.lock").exists()
    if lock_present:
        raise InvoiceCollectionIncompleteError(
            f"Lock presente em {collection_id} — publicação ainda em escrita."
        )

    manifesto_path = directory / "manifesto.json"
    if not manifesto_path.is_file():
        raise InvoiceCollectionIncompleteError(
            f"manifesto.json ausente em {collection_id} "
            "(ausência de manifesto ≠ zero notas)."
        )
    _assert_safe_file(manifesto_path, directory)

    first_manifest_hash = _sha256_file(manifesto_path, max_bytes=_MAX_MANIFEST_BYTES)
    if stability_wait_seconds > 0:
        time.sleep(stability_wait_seconds)
    second_manifest_hash = _sha256_file(manifesto_path, max_bytes=_MAX_MANIFEST_BYTES)
    if first_manifest_hash != second_manifest_hash:
        raise InvoiceCollectionIncompleteError(
            f"manifesto.json instável em {collection_id}."
        )

    manifesto = _read_manifest(manifesto_path)
    _validate_manifest_scope(manifesto, collection_id=collection_id, directory=directory)

    status_raw = str(manifesto.get("status_validacao") or "").strip().upper()
    observation_status = manifest_status_to_observation_status(status_raw)
    if observation_status is None:
        raise InvoiceCollectionReadError(
            f"status_validacao não suportado: {status_raw!r}."
        )

    document_date = _parse_document_date(manifesto.get("data_documento"))
    _assert_document_date_matches_path(directory, document_date)

    observed_at = _parse_optional_datetime(manifesto.get("executado_em"))
    source_prepared_at = _parse_required_datetime(
        manifesto.get("publicado_em_preparacao_utc"),
        field_name="publicado_em_preparacao_utc",
    )

    if observation_status == OBSERVATION_STATUS_EMPTY_SIGNALED_BY_SAP:
        if manifesto.get("sem_xlsx") is not True and manifesto.get("arquivo_original"):
            raise InvoiceCollectionReadError(
                "Manifesto SEM_REGISTROS não pode declarar XLSX."
            )
        xlsx_files = _list_xlsx(directory)
        if xlsx_files:
            raise InvoiceCollectionReadError(
                "Manifesto SEM_REGISTROS com XLSX presente — inconsistência."
            )
        _assert_deadline(started)
        logger.info(
            "myweg_invoice_empty_collection collection_id=%s document_date=%s",
            collection_id,
            document_date.isoformat(),
        )
        return InvoiceCollectionArtifacts(
            collection_id=collection_id,
            directory=directory,
            document_date=document_date,
            observation_status=OBSERVATION_STATUS_EMPTY_SIGNALED_BY_SAP,
            observed_at=observed_at,
            source_prepared_at=source_prepared_at,
            source_sha256=None,
            manifesto=manifesto,
            records=[],
            xlsx_name=None,
        )

    # with_records
    xlsx_name = str(manifesto.get("arquivo_original") or "").strip()
    if not xlsx_name:
        raise InvoiceCollectionIncompleteError(
            f"arquivo_original ausente no manifesto VALIDADO ({collection_id})."
        )
    xlsx_path = directory / xlsx_name
    if not xlsx_path.is_file():
        raise InvoiceCollectionIncompleteError(
            f"XLSX ausente: {xlsx_name} (coleta incompleta ≠ zero notas)."
        )
    _assert_safe_file(xlsx_path, directory)
    _assert_zip_bomb_limits(xlsx_path)

    declared_sha = str(manifesto.get("sha256") or "").strip().lower()
    if len(declared_sha) != 64:
        raise InvoiceCollectionReadError("sha256 do manifesto inválido.")

    first_xlsx = _sha256_file(xlsx_path, max_bytes=_MAX_XLSX_BYTES)
    if stability_wait_seconds > 0:
        time.sleep(min(0.25, stability_wait_seconds))
    second_xlsx = _sha256_file(xlsx_path, max_bytes=_MAX_XLSX_BYTES)
    if first_xlsx != second_xlsx:
        raise InvoiceCollectionIncompleteError(
            f"XLSX instável em {collection_id}."
        )
    if first_xlsx != declared_sha:
        raise InvoiceCollectionReadError(
            "SHA-256 do XLSX diverge do manifesto (arquivo alterado após publicação)."
        )

    records = _read_xlsx_records(xlsx_path)
    declared_lines = manifesto.get("quantidade_linhas")
    if declared_lines is not None and int(declared_lines) != len(records):
        raise InvoiceCollectionReadError(
            f"quantidade_linhas={declared_lines} ≠ linhas XLSX={len(records)}."
        )

    _assert_deadline(started)
    logger.info(
        "myweg_invoice_collection_loaded collection_id=%s document_date=%s records=%s",
        collection_id,
        document_date.isoformat(),
        len(records),
    )
    return InvoiceCollectionArtifacts(
        collection_id=collection_id,
        directory=directory,
        document_date=document_date,
        observation_status=OBSERVATION_STATUS_WITH_RECORDS,
        observed_at=observed_at,
        source_prepared_at=source_prepared_at,
        source_sha256=first_xlsx,
        manifesto=manifesto,
        records=records,
        xlsx_name=xlsx_name,
    )


def _assert_deadline(started: float) -> None:
    if time.monotonic() - started > _MAX_PROCESS_SECONDS:
        raise InvoiceCollectionReadError("Tempo máximo de processamento excedido.")


def _assert_safe_dir(directory: Path) -> Path:
    if directory.is_symlink():
        raise InvoiceCollectionReadError(f"Diretório symlink rejeitado: {directory}")
    resolved = directory.expanduser().resolve(strict=False)
    if not resolved.is_dir():
        raise InvoiceCollectionIncompleteError(f"Coleta inexistente: {resolved}")
    return resolved


def _assert_safe_file(path: Path, root: Path) -> None:
    if path.is_symlink():
        raise InvoiceCollectionReadError(f"Symlink rejeitado: {path.name}")
    resolved = path.resolve(strict=False)
    root_resolved = root.resolve(strict=False)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise InvoiceCollectionReadError(
            f"Caminho fora da pasta da coleta: {path.name}"
        ) from exc
    if not resolved.is_file():
        raise InvoiceCollectionIncompleteError(f"Arquivo inválido: {path.name}")


def _list_xlsx(directory: Path) -> list[Path]:
    return [
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() == ".xlsx" and not path.is_symlink()
    ]


def _sha256_file(path: Path, *, max_bytes: int) -> str:
    size = path.stat().st_size
    if size > max_bytes:
        raise InvoiceCollectionReadError(
            f"Arquivo excede limite ({size} > {max_bytes}): {path.name}"
        )
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_zip_bomb_limits(path: Path) -> None:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            total = 0
            for info in archive.infolist():
                total += int(info.file_size)
                if total > _MAX_UNCOMPRESSED_ZIP_BYTES:
                    raise InvoiceCollectionReadError(
                        "XLSX excede limite de descompactação (possível zip bomb)."
                    )
    except zipfile.BadZipFile as exc:
        raise InvoiceCollectionReadError("XLSX corrompido ou não é ZIP válido.") from exc


def _read_manifest(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InvoiceCollectionReadError(
            f"manifesto.json ilegível: {exc.__class__.__name__}"
        ) from exc
    if not isinstance(data, dict):
        raise InvoiceCollectionReadError("manifesto.json deve ser um objeto.")
    return data


def _validate_manifest_scope(
    manifesto: dict[str, Any], *, collection_id: str, directory: Path
) -> None:
    schema = manifesto.get("schema_version")
    try:
        if int(schema) != _SCHEMA_VERSION:
            raise InvoiceCollectionReadError(
                f"schema_version não suportado: {schema!r}."
            )
    except (TypeError, ValueError) as exc:
        raise InvoiceCollectionReadError("schema_version inválido.") from exc

    manifest_collection = str(manifesto.get("collection_id") or "").strip()
    if manifest_collection != collection_id:
        raise InvoiceCollectionReadError(
            "collection_id do manifesto diverge do nome da pasta."
        )
    if str(manifesto.get("origem") or "").strip() != "MyWEG":
        raise InvoiceCollectionReadError("origem deve ser MyWEG.")
    if str(manifesto.get("tipo_relatorio") or "").strip() != "notas_fiscais_emitidas":
        raise InvoiceCollectionReadError(
            "tipo_relatorio deve ser notas_fiscais_emitidas."
        )

    unidade = _normalize_branch(manifesto.get("unidade_delpi"))
    if unidade != ALLOWED_BRANCH:
        raise InvoiceCollectionReadError(
            f"unidade_delpi={unidade!r} fora do escopo (somente 02)."
        )
    if str(manifesto.get("empresa_myweg") or "").strip() != MYWEG_COMPANY_CODE:
        raise InvoiceCollectionReadError("empresa_myweg divergente.")
    if str(manifesto.get("centro") or "").strip() != MYWEG_WORK_CENTER:
        raise InvoiceCollectionReadError("centro divergente.")
    if str(manifesto.get("fornecedor") or "").strip() != MYWEG_SUPPLIER_CODE:
        raise InvoiceCollectionReadError("fornecedor divergente.")

    # Identidade da pasta: filial-02/empresa-1009/centro-1106/fornecedor-50471/...
    parts = {part.name for part in directory.parents}
    expected = {
        f"filial-{ALLOWED_BRANCH}",
        f"empresa-{MYWEG_COMPANY_CODE}",
        f"centro-{MYWEG_WORK_CENTER}",
        f"fornecedor-{MYWEG_SUPPLIER_CODE}",
    }
    if not expected.issubset(parts):
        # Aceita fixture flat se manifesto ok; loga aviso.
        logger.warning(
            "myweg_invoice_path_identity_soft collection_id=%s missing=%s",
            collection_id,
            sorted(expected - parts),
        )


def _normalize_branch(value: Any) -> str:
    text = str(value or "").strip()
    if text.isdigit():
        return text.zfill(2)
    return text


def _parse_document_date(value: Any) -> date:
    text = str(value or "").strip()
    if not text:
        raise InvoiceCollectionReadError("data_documento ausente no manifesto.")
    try:
        if "/" in text:
            day, month, year = text.split("/")
            return date(int(year), int(month), int(day))
        return date.fromisoformat(text[:10])
    except (TypeError, ValueError) as exc:
        raise InvoiceCollectionReadError(f"data_documento inválida: {value!r}") from exc


def _assert_document_date_matches_path(directory: Path, document_date: date) -> None:
    parent = directory.parent.name
    if parent.startswith("data-documento="):
        declared = parent.split("=", 1)[1].strip()
        if declared != document_date.isoformat():
            raise InvoiceCollectionReadError(
                f"Pasta {parent} diverge de data_documento={document_date.isoformat()}."
            )


def _parse_optional_datetime(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvoiceCollectionReadError(f"executado_em inválido: {value!r}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_SAO_PAULO)
    return dt


def _parse_required_datetime(value: Any, *, field_name: str) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise InvoiceCollectionReadError(f"{field_name} ausente no manifesto.")
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvoiceCollectionReadError(f"{field_name} inválido: {value!r}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_SAO_PAULO)
    return dt


def _read_xlsx_records(path: Path) -> list[dict[str, Any]]:
    try:
        workbook = load_workbook(path, read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001 — openpyxl varia exceções
        raise InvoiceCollectionReadError(
            f"XLSX ilegível: {exc.__class__.__name__}"
        ) from exc

    try:
        sheet = workbook.active
        rows_iter = sheet.iter_rows(values_only=True)
        try:
            header_row = next(rows_iter)
        except StopIteration as exc:
            raise InvoiceCollectionReadError("XLSX sem cabeçalho.") from exc

        headers = [str(cell or "").strip() for cell in header_row]
        if tuple(headers[:7]) != EXPECTED_HEADERS:
            raise InvoiceCollectionReadError(
                f"Cabeçalho XLSX inválido: {headers[:7]!r}."
            )

        records: list[dict[str, Any]] = []
        for excel_row_no, row in enumerate(rows_iter, start=2):
            if excel_row_no - 1 > _MAX_ROWS:
                raise InvoiceCollectionReadError(
                    f"XLSX excede limite de {_MAX_ROWS} linhas."
                )
            values = list(row[:7]) if row else []
            if not any(cell is not None and str(cell).strip() != "" for cell in values):
                continue
            while len(values) < 7:
                values.append(None)

            invoice_number = _as_text_preserve(values[0])
            invoice_series = _as_text_preserve(values[1])
            material_weg = _as_text_preserve(values[2])
            material_description = _as_text_preserve(values[3])
            quantity = _parse_quantity(values[4], row_no=excel_row_no)
            source_unit = _as_text_preserve(values[5]).upper()
            departure_date = _parse_departure_date(values[6], row_no=excel_row_no)

            if not invoice_number or not invoice_series or not material_weg:
                raise InvoiceCollectionReadError(
                    f"Linha {excel_row_no}: NF/série/material obrigatórios."
                )
            if not source_unit:
                raise InvoiceCollectionReadError(
                    f"Linha {excel_row_no}: unidade ausente."
                )

            quantity_un, unit_comparability = quantity_to_un(
                quantity_original=quantity, source_unit=source_unit
            )
            if quantity_un is None:
                raise InvoiceCollectionReadError(
                    f"Linha {excel_row_no}: unidade {source_unit!r} não comparável."
                )

            records.append(
                {
                    "source_line_no": excel_row_no,
                    "invoice_number": invoice_number,
                    "invoice_series": invoice_series,
                    "material_weg": material_weg,
                    "material_description": material_description,
                    "quantity_original": decimal_to_canonical_str(quantity),
                    "source_unit": source_unit,
                    "quantity_un": decimal_to_canonical_str(quantity_un),
                    "unit_comparability": unit_comparability,
                    "departure_date": departure_date.isoformat(),
                }
            )
        if not records:
            raise InvoiceCollectionReadError(
                "XLSX VALIDADO sem linhas de dados — inconsistência."
            )
        return records
    finally:
        workbook.close()


def _as_text_preserve(value: Any) -> str:
    """Preserva zeros à esquerda; evita float científico."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        as_dec = Decimal(str(value))
        return decimal_to_canonical_str(as_dec)
    if isinstance(value, Decimal):
        return decimal_to_canonical_str(value)
    text = str(value).strip()
    if text.endswith(".0") and text.replace(".", "", 1).isdigit():
        return text[:-2]
    return text


def _parse_quantity(value: Any, *, row_no: int) -> Decimal:
    try:
        if isinstance(value, Decimal):
            qty = value
        elif isinstance(value, (int, float)):
            qty = Decimal(str(value))
        else:
            text = str(value or "").strip().replace(",", ".")
            qty = Decimal(text)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise InvoiceCollectionReadError(
            f"Linha {row_no}: quantidade inválida ({value!r})."
        ) from exc
    if qty <= 0:
        raise InvoiceCollectionReadError(
            f"Linha {row_no}: quantidade deve ser positiva."
        )
    return qty


def _parse_departure_date(value: Any, *, row_no: int) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    if not text:
        raise InvoiceCollectionReadError(f"Linha {row_no}: Data de Saída ausente.")
    try:
        if "/" in text:
            day, month, year = text.split("/")
            return date(int(year), int(month), int(day))
        return date.fromisoformat(text[:10])
    except (TypeError, ValueError) as exc:
        raise InvoiceCollectionReadError(
            f"Linha {row_no}: Data de Saída inválida ({value!r})."
        ) from exc
