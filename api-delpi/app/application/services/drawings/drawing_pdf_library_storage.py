from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings

_PRODUCT_CODE_PATTERN = re.compile(r"^[\dA-Z]+(?:-\d+)?$", re.IGNORECASE)
_REVISION_SUFFIX_PATTERN = re.compile(r"_R(\d+)$", re.IGNORECASE)
_NUMERIC_PREFIX_PATTERN = re.compile(r"^(\d+)")
_VARIANT_SUFFIX_PATTERN = re.compile(r"^(\d+)-(\d+)$")
_ALLOWED_SORT_FIELDS = frozenset(
    {"product_code", "filename", "modified_at", "size_bytes", "revision", "file_kind"}
)
_ALLOWED_FILE_KINDS = frozenset({"exact", "revision", "variant", "other"})
_MAX_PAGE_SIZE = 500


class DrawingPdfLibraryStorageError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class DrawingPdfMatch:
    product_code: str
    filename: str
    path: Path
    size_bytes: int
    modified_at: datetime
    revision: str | None = None
    variant_suffix: str | None = None

    def to_metadata_dict(self) -> dict[str, Any]:
        return {
            "product_code": self.product_code,
            "found": True,
            "filename": self.filename,
            "revision": self.revision,
            "variant_suffix": self.variant_suffix,
            "size_bytes": self.size_bytes,
            "modified_at": self.modified_at.astimezone(timezone.utc).isoformat(),
            "media_type": "application/pdf",
        }


@dataclass(frozen=True, slots=True)
class DrawingPdfCatalogEntry:
    product_code: str
    filename: str
    file_kind: str
    size_bytes: int
    modified_at: datetime
    revision: str | None = None
    variant_suffix: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "product_code": self.product_code,
            "filename": self.filename,
            "file_kind": self.file_kind,
            "revision": self.revision,
            "variant_suffix": self.variant_suffix,
            "size_bytes": self.size_bytes,
            "modified_at": self.modified_at.astimezone(timezone.utc).isoformat(),
            "media_type": "application/pdf",
            "drawing_metadata_path": f"/products/{self.product_code}/drawing",
            "drawing_pdf_path": f"/products/{self.product_code}/drawing/pdf",
        }


class DrawingPdfLibraryStorage:
    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir or settings.DRAWING_PDF_LIBRARY_DIR)

    def normalize_product_code(self, code: str) -> str:
        normalized = (code or "").strip().upper()
        if not normalized:
            raise DrawingPdfLibraryStorageError("Código do produto é obrigatório.")
        if ".." in normalized or "/" in normalized or "\\" in normalized:
            raise DrawingPdfLibraryStorageError("Código do produto inválido.")
        if not _PRODUCT_CODE_PATTERN.fullmatch(normalized):
            raise DrawingPdfLibraryStorageError("Código do produto inválido.")
        return normalized

    def find_drawing(self, product_code: str) -> DrawingPdfMatch | None:
        normalized = self.normalize_product_code(product_code)
        if not self.base_dir.is_dir():
            return None

        exact = self.base_dir / f"{normalized}.pdf"
        if exact.is_file():
            return self._build_match(normalized, exact)

        numeric_prefix = self._numeric_prefix(normalized)
        if not numeric_prefix:
            return None

        candidates: list[Path] = []
        for path in self.base_dir.glob(f"{numeric_prefix}*.pdf"):
            if not path.is_file():
                continue
            stem = path.stem.upper()
            if self._stem_matches_request(stem, normalized, numeric_prefix):
                candidates.append(path)

        if not candidates:
            return None

        selected = min(candidates, key=lambda item: self._candidate_rank(item, normalized))
        return self._build_match(normalized, selected)

    def resolve_pdf_path(self, product_code: str) -> Path:
        match = self.find_drawing(product_code)
        if match is None:
            raise DrawingPdfLibraryStorageError(
                "Desenho PDF não encontrado para o produto informado."
            )

        resolved = match.path.resolve()
        base = self.base_dir.resolve()
        if not str(resolved).startswith(str(base)):
            raise DrawingPdfLibraryStorageError("Caminho de arquivo inválido.")
        if not resolved.is_file():
            raise DrawingPdfLibraryStorageError(
                "Desenho PDF não encontrado para o produto informado."
            )
        return resolved

    def list_catalog(
        self,
        *,
        code: str | None = None,
        code_exact: bool = False,
        filename: str | None = None,
        revision: str | None = None,
        file_kind: str | None = None,
        has_variant: bool | None = None,
        has_revision: bool | None = None,
        modified_from: datetime | None = None,
        modified_to: datetime | None = None,
        min_size_bytes: int | None = None,
        max_size_bytes: int | None = None,
        page: int = 1,
        page_size: int = 50,
        sort: str = "product_code",
        direction: str = "asc",
    ) -> dict[str, Any]:
        page = max(1, int(page or 1))
        page_size = max(1, min(int(page_size or 50), _MAX_PAGE_SIZE))
        sort_field = str(sort or "product_code").strip().lower()
        sort_direction = str(direction or "asc").strip().lower()

        if sort_field not in _ALLOWED_SORT_FIELDS:
            raise DrawingPdfLibraryStorageError(
                f"Campo de ordenação inválido: {sort_field}."
            )
        if sort_direction not in {"asc", "desc"}:
            raise DrawingPdfLibraryStorageError("Direção de ordenação inválida.")

        normalized_file_kind = str(file_kind or "").strip().lower() or None
        if normalized_file_kind and normalized_file_kind not in _ALLOWED_FILE_KINDS:
            raise DrawingPdfLibraryStorageError("Tipo de arquivo inválido.")

        code_filter = str(code or "").strip().upper() or None
        filename_filter = str(filename or "").strip().upper() or None
        revision_filter = self._normalize_revision_filter(revision)

        library_available = self.base_dir.is_dir()
        entries = self._scan_catalog_entries() if library_available else []
        filtered = [
            entry
            for entry in entries
            if self._catalog_entry_matches(
                entry,
                code_filter=code_filter,
                code_exact=code_exact,
                filename_filter=filename_filter,
                revision_filter=revision_filter,
                file_kind=normalized_file_kind,
                has_variant=has_variant,
                has_revision=has_revision,
                modified_from=modified_from,
                modified_to=modified_to,
                min_size_bytes=min_size_bytes,
                max_size_bytes=max_size_bytes,
            )
        ]

        reverse = sort_direction == "desc"
        filtered.sort(
            key=lambda entry: self._catalog_sort_key(entry, sort_field),
            reverse=reverse,
        )

        total = len(filtered)
        total_pages = (total + page_size - 1) // page_size if page_size else 0
        start = (page - 1) * page_size
        end = start + page_size
        page_items = filtered[start:end]

        return {
            "items": [entry.to_dict() for entry in page_items],
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "summary": {
                "library_available": library_available,
                "library_dir": str(self.base_dir),
                "scanned_files": len(entries),
                "matched_files": total,
                "filters_applied": self._catalog_filters_summary(
                    code=code_filter,
                    code_exact=code_exact,
                    filename=filename_filter,
                    revision=revision_filter,
                    file_kind=normalized_file_kind,
                    has_variant=has_variant,
                    has_revision=has_revision,
                    modified_from=modified_from,
                    modified_to=modified_to,
                    min_size_bytes=min_size_bytes,
                    max_size_bytes=max_size_bytes,
                ),
            },
        }

    def _scan_catalog_entries(self) -> list[DrawingPdfCatalogEntry]:
        entries: list[DrawingPdfCatalogEntry] = []

        for path in sorted(self.base_dir.glob("*.pdf")):
            if not path.is_file():
                continue

            resolved = path.resolve()
            base = self.base_dir.resolve()
            if not str(resolved).startswith(str(base)):
                continue

            entries.append(self._build_catalog_entry(path))

        return entries

    def _build_catalog_entry(self, path: Path) -> DrawingPdfCatalogEntry:
        stat = path.stat()
        stem = path.stem.upper()
        product_code, revision, variant_suffix, file_kind = self._parse_filename_stem(stem)

        return DrawingPdfCatalogEntry(
            product_code=product_code,
            filename=path.name,
            file_kind=file_kind,
            revision=revision,
            variant_suffix=variant_suffix,
            size_bytes=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        )

    def _parse_filename_stem(
        self,
        stem: str,
    ) -> tuple[str, str | None, str | None, str]:
        revision_match = _REVISION_SUFFIX_PATTERN.search(stem)
        if revision_match:
            revision = revision_match.group(1).lstrip("0") or "0"
            base_code = stem[: revision_match.start()].rstrip("_") or stem
            return base_code, revision, None, "revision"

        variant_match = _VARIANT_SUFFIX_PATTERN.fullmatch(stem)
        if variant_match:
            return stem, None, variant_match.group(2), "variant"

        if _PRODUCT_CODE_PATTERN.fullmatch(stem):
            return stem, None, None, "exact"

        return stem, None, None, "other"

    def _catalog_entry_matches(
        self,
        entry: DrawingPdfCatalogEntry,
        *,
        code_filter: str | None,
        code_exact: bool,
        filename_filter: str | None,
        revision_filter: str | None,
        file_kind: str | None,
        has_variant: bool | None,
        has_revision: bool | None,
        modified_from: datetime | None,
        modified_to: datetime | None,
        min_size_bytes: int | None,
        max_size_bytes: int | None,
    ) -> bool:
        if code_filter:
            haystack = entry.product_code.upper()
            if code_exact and haystack != code_filter:
                return False
            if not code_exact and not haystack.startswith(code_filter):
                return False

        if filename_filter and filename_filter not in entry.filename.upper():
            return False

        if revision_filter is not None and entry.revision != revision_filter:
            return False

        if file_kind and entry.file_kind != file_kind:
            return False

        if has_variant is True and not entry.variant_suffix:
            return False
        if has_variant is False and entry.variant_suffix:
            return False

        if has_revision is True and not entry.revision:
            return False
        if has_revision is False and entry.revision:
            return False

        if modified_from and entry.modified_at < self._ensure_utc(modified_from):
            return False
        if modified_to and entry.modified_at > self._ensure_utc(modified_to):
            return False

        if min_size_bytes is not None and entry.size_bytes < min_size_bytes:
            return False
        if max_size_bytes is not None and entry.size_bytes > max_size_bytes:
            return False

        return True

    def _catalog_sort_key(
        self,
        entry: DrawingPdfCatalogEntry,
        sort_field: str,
    ) -> tuple[Any, ...]:
        if sort_field == "filename":
            return (entry.filename.upper(), entry.product_code)
        if sort_field == "modified_at":
            return (entry.modified_at.timestamp(), entry.product_code)
        if sort_field == "size_bytes":
            return (entry.size_bytes, entry.product_code)
        if sort_field == "revision":
            revision_number = int(entry.revision) if entry.revision and entry.revision.isdigit() else -1
            return (revision_number, entry.product_code)
        if sort_field == "file_kind":
            return (entry.file_kind, entry.product_code)
        return (entry.product_code, entry.filename.upper())

    def _catalog_filters_summary(self, **filters: Any) -> dict[str, Any]:
        applied: dict[str, Any] = {}

        for key, value in filters.items():
            if value is None:
                continue
            if isinstance(value, datetime):
                applied[key] = value.astimezone(timezone.utc).isoformat()
            else:
                applied[key] = value

        return applied

    def _normalize_revision_filter(self, revision: str | None) -> str | None:
        normalized = str(revision or "").strip()
        if not normalized:
            return None
        return normalized.lstrip("0") or "0"

    def _ensure_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _numeric_prefix(self, code: str) -> str | None:
        match = _NUMERIC_PREFIX_PATTERN.match(code)
        return match.group(1) if match else None

    def _stem_matches_request(self, stem: str, requested_code: str, numeric_prefix: str) -> bool:
        if stem == requested_code:
            return True
        if stem == numeric_prefix:
            return True
        if _REVISION_SUFFIX_PATTERN.search(stem) and stem.startswith(numeric_prefix):
            return True
        if stem.startswith(f"{numeric_prefix}-") and stem[len(numeric_prefix) + 1 :].isdigit():
            return True
        return False

    def _candidate_rank(self, path: Path, requested_code: str) -> tuple[int, int, int, float]:
        stem = path.stem.upper()
        if stem == requested_code:
            return (0, 0, 0, 0.0)

        numeric_prefix = self._numeric_prefix(requested_code) or requested_code
        if stem == numeric_prefix:
            return (1, 0, 0, 0.0)

        revision_match = _REVISION_SUFFIX_PATTERN.search(stem)
        if revision_match:
            revision = int(revision_match.group(1))
            return (2, 0, -revision, 0.0)

        variant_match = re.fullmatch(rf"{re.escape(numeric_prefix)}-(\d+)", stem)
        if variant_match:
            variant = int(variant_match.group(1))
            return (3, variant, 0, 0.0)

        return (9, 0, 0, -path.stat().st_mtime)

    def _build_match(self, requested_code: str, path: Path) -> DrawingPdfMatch:
        stat = path.stat()
        stem = path.stem.upper()
        revision = None
        variant_suffix = None

        revision_match = _REVISION_SUFFIX_PATTERN.search(stem)
        if revision_match:
            revision = revision_match.group(1).lstrip("0") or "0"

        variant_match = re.fullmatch(
            rf"{self._numeric_prefix(requested_code) or requested_code}-(\d+)",
            stem,
        )
        if variant_match:
            variant_suffix = variant_match.group(1)

        return DrawingPdfMatch(
            product_code=requested_code,
            filename=path.name,
            path=path,
            size_bytes=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            revision=revision,
            variant_suffix=variant_suffix,
        )
