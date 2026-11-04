"""Leitura e validação de pastas normalizadas MyWEG (sem alterar o ETL)."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from production_control_app.jobs.myweg_needs_publisher import REQUIRED_ARTIFACTS

_SAO_PAULO = ZoneInfo("America/Sao_Paulo")
_COLLECTION_TS_RE = re.compile(
    r"^(?P<a>\d{8}_\d{6})_(?P<b>\d{8}_\d{6})_EXPORT_(?P<c>\d{8}_\d{6})$"
)


@dataclass(frozen=True)
class CollectionArtifacts:
    collection_id: str
    directory: Path
    file_hashes: dict[str, str]
    resumo: dict[str, Any]
    source_rows: list[dict[str, Any]]
    collected_at: datetime
    lock_present: bool


class CollectionIncompleteError(ValueError):
    """Pasta incompleta, instável ou malformada."""


def list_collection_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        raise CollectionIncompleteError(f"Raiz de normalizados inexistente: {root}")
    return sorted(
        [path for path in root.iterdir() if path.is_dir() and not path.name.startswith(".")],
        key=lambda path: path.name,
    )


def select_latest_eligible_dir(root: Path) -> Path:
    dirs = list_collection_dirs(root)
    if not dirs:
        raise CollectionIncompleteError("Nenhuma pasta de coleta encontrada.")
    # Preferência: pasta com os 4 artefatos; senão a mais recente pelo nome.
    complete = [path for path in dirs if _has_required_names(path)]
    if complete:
        return complete[-1]
    return dirs[-1]


def load_collection(
    directory: Path,
    *,
    stability_wait_seconds: float = 0.75,
) -> CollectionArtifacts:
    if not directory.is_dir():
        raise CollectionIncompleteError(f"Coleta inexistente: {directory}")
    collection_id = directory.name.strip()
    if not collection_id:
        raise CollectionIncompleteError("collection_id vazio.")

    lock_present = (directory / ".lock").exists() or (directory / "etl.lock").exists()
    if lock_present:
        raise CollectionIncompleteError(
            f"Lock de ETL presente em {directory.name} — coleta ainda em escrita."
        )

    missing = [name for name in REQUIRED_ARTIFACTS if not (directory / name).is_file()]
    if missing:
        raise CollectionIncompleteError(
            f"Arquivos ausentes em {collection_id}: {', '.join(missing)}"
        )

    first_hashes = _hash_required_files(directory)
    if stability_wait_seconds > 0:
        time.sleep(stability_wait_seconds)
    second_hashes = _hash_required_files(directory)
    if first_hashes != second_hashes:
        raise CollectionIncompleteError(
            f"Arquivos instáveis em {collection_id} (hashes divergiram entre leituras)."
        )

    resumo_path = directory / "resumo.json"
    try:
        resumo = json.loads(resumo_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CollectionIncompleteError(
            f"resumo.json ilegível em {collection_id}: {exc.__class__.__name__}"
        ) from exc
    if not isinstance(resumo, dict):
        raise CollectionIncompleteError("resumo.json deve ser um objeto JSON.")

    source_rows = _read_csv_rows(directory / "necessidades_tratadas.csv")
    if not source_rows:
        raise CollectionIncompleteError(
            f"necessidades_tratadas.csv sem registros em {collection_id}."
        )

    declared_count = resumo.get("record_count") or resumo.get("total_registros")
    if declared_count is not None:
        try:
            if int(declared_count) != len(source_rows):
                raise CollectionIncompleteError(
                    f"Inconsistência de linhas: resumo={declared_count} csv={len(source_rows)}."
                )
        except (TypeError, ValueError) as exc:
            raise CollectionIncompleteError("record_count inválido no resumo.json.") from exc

    collected_at = _resolve_collected_at(collection_id=collection_id, resumo=resumo)

    return CollectionArtifacts(
        collection_id=collection_id,
        directory=directory,
        file_hashes=second_hashes,
        resumo=resumo,
        source_rows=source_rows,
        collected_at=collected_at,
        lock_present=False,
    )


def _has_required_names(directory: Path) -> bool:
    return all((directory / name).is_file() for name in REQUIRED_ARTIFACTS)


def _hash_required_files(directory: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for name in REQUIRED_ARTIFACTS:
        path = directory / name
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        hashes[name] = digest.hexdigest()
    return hashes


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise CollectionIncompleteError("CSV sem cabeçalho.")
            rows: list[dict[str, Any]] = []
            for raw in reader:
                if raw is None:
                    continue
                cleaned = {
                    str(key).strip(): (value.strip() if isinstance(value, str) else value)
                    for key, value in raw.items()
                    if key is not None
                }
                if not any(str(v or "").strip() for v in cleaned.values()):
                    continue
                rows.append(cleaned)
            return rows
    except (OSError, UnicodeError, csv.Error) as exc:
        raise CollectionIncompleteError(
            f"Falha ao ler CSV: {exc.__class__.__name__}"
        ) from exc


def _resolve_collected_at(*, collection_id: str, resumo: dict[str, Any]) -> datetime:
    for key in ("collected_at", "collectedAt", "data_coleta", "coleta_em"):
        value = resumo.get(key)
        if value:
            parsed = _parse_aware_datetime(str(value))
            if parsed is not None:
                return parsed

    match = _COLLECTION_TS_RE.match(collection_id)
    if match:
        # Convenção observada: segundo bloco = instante da coleta/export origem.
        stamp = match.group("b")
        parsed = datetime.strptime(stamp, "%Y%m%d_%H%M%S").replace(tzinfo=_SAO_PAULO)
        return parsed

    raise CollectionIncompleteError(
        "Não foi possível comprovar collected_at (resumo.json / collection_id)."
    )


def _parse_aware_datetime(value: str) -> datetime | None:
    text = value.strip().replace("Z", "+00:00")
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y%m%d_%H%M%S", "%d/%m/%Y %H:%M:%S"):
            try:
                parsed = datetime.strptime(text, fmt).replace(tzinfo=_SAO_PAULO)
                return parsed
            except ValueError:
                continue
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_SAO_PAULO)
    return parsed
