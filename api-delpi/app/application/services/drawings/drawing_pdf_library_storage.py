from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings

_PRODUCT_CODE_PATTERN = re.compile(r"^[\dA-Z]+(?:-\d+)?$", re.IGNORECASE)
_REVISION_SUFFIX_PATTERN = re.compile(r"_R(\d+)$", re.IGNORECASE)
_NUMERIC_PREFIX_PATTERN = re.compile(r"^(\d+)")


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

    def to_metadata_dict(self) -> dict:
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
            raise DrawingPdfLibraryStorageError("Desenho PDF não encontrado para o produto informado.")

        resolved = match.path.resolve()
        base = self.base_dir.resolve()
        if not str(resolved).startswith(str(base)):
            raise DrawingPdfLibraryStorageError("Caminho de arquivo inválido.")
        if not resolved.is_file():
            raise DrawingPdfLibraryStorageError("Desenho PDF não encontrado para o produto informado.")
        return resolved

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

        variant_match = re.fullmatch(rf"{self._numeric_prefix(requested_code) or requested_code}-(\d+)", stem)
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
