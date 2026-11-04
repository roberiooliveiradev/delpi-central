"""Leitura e validação de pastas normalizadas MyWEG (sem alterar o ETL)."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
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


def _detect_csv_delimiter(sample: str) -> str:
    """Detecta delimitador de CSV (Excel BR costuma usar ';')."""
    if not sample.strip():
        return ","
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        if dialect.delimiter:
            return dialect.delimiter
    except csv.Error:
        pass
    header = sample.splitlines()[0] if sample.splitlines() else sample
    scores = {delim: header.count(delim) for delim in (",", ";", "\t", "|")}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else ","


def _fold_header(name: str) -> str:
    """Normaliza cabeçalho para comparação (sem acento, lower, snake)."""
    text = unicodedata.normalize("NFKD", str(name or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.strip().lower()
    out: list[str] = []
    for ch in text:
        if ch.isalnum():
            out.append(ch)
        else:
            out.append("_")
    folded = "".join(out)
    while "__" in folded:
        folded = folded.replace("__", "_")
    return folded.strip("_")


# Cabeçalhos ETL / planilha → campos canônicos E1.
_HEADER_CANONICAL: dict[str, str] = {
    "material_weg_tratado": "material_weg_tratado",
    "material_weg": "material_weg_tratado",
    "material": "material_weg_tratado",
    "codigo_referencia_weg": "codigo_referencia_weg",
    "codigo_referencia": "codigo_referencia_weg",
    "codigo_de_referencia_weg": "codigo_referencia_weg",
    "referencia_weg": "codigo_referencia_weg",
    "origem_material_weg": "origem_material_weg",
    "origem_material": "origem_material_weg",
    "origem": "origem_material_weg",
    "quantidade": "quantidade",
    "quantidade_original_un": "quantidade_original_un",
    "quantidade_original": "quantidade",
    "qtde": "quantidade",
    "qtd": "quantidade",
    "unidade": "unidade",
    "um": "unidade",
    "data_remessa": "data_remessa",
    "data_de_remessa": "data_remessa",
    "dt_remessa": "data_remessa",
    "remessa": "data_remessa",
    "documento": "documento",
    "doc": "documento",
    "linha_fonte": "linha_fonte",
    "linha": "linha_fonte",
    "n_linha": "linha_fonte",
    "num_linha": "linha_fonte",
    "assinatura_registro": "assinatura_registro",
    "assinatura": "assinatura_registro",
    "hash_linha": "assinatura_registro",
    "rastreabilidade": "rastreabilidade",
    "traceability": "rastreabilidade",
}


def _remap_row_headers(raw: Mapping[str, Any]) -> dict[str, Any]:
    remapped: dict[str, Any] = {}
    for key, value in raw.items():
        if key is None:
            continue
        canonical = _HEADER_CANONICAL.get(_fold_header(str(key)), str(key).strip())
        # Prefer first non-empty when aliases colidem.
        if canonical in remapped and str(remapped[canonical] or "").strip():
            continue
        remapped[canonical] = value.strip() if isinstance(value, str) else value
    return remapped


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            sample = handle.read(8192)
            handle.seek(0)
            delimiter = _detect_csv_delimiter(sample)
            reader = csv.DictReader(handle, delimiter=delimiter)
            if not reader.fieldnames:
                raise CollectionIncompleteError("CSV sem cabeçalho.")
            rows: list[dict[str, Any]] = []
            for data_index, raw in enumerate(reader):
                if raw is None:
                    continue
                cleaned = _remap_row_headers(
                    {
                        str(key).strip(): (
                            value.strip() if isinstance(value, str) else value
                        )
                        for key, value in raw.items()
                        if key is not None
                    }
                )
                if not any(str(v or "").strip() for v in cleaned.values()):
                    continue
                # Planilha: cabeçalho = linha 1; primeira data = linha 2.
                if not str(cleaned.get("linha_fonte") or "").strip():
                    cleaned["linha_fonte"] = str(data_index + 2)
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
