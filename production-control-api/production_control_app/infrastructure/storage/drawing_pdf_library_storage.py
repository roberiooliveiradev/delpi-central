"""Resolve o PDF do desenho na pasta do FILESERVER montada no container do PCP."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from production_control_app.config import settings
from production_control_app.domain.errors import DrawingNotFound
from production_control_app.domain.product_drawing_pdf import DrawingFile

_CODE_PATTERN = re.compile(r"^[\dA-Z]+(?:-\d+)?$")
_REVISION_SUFFIX_PATTERN = re.compile(r"_R(\d+)$")
_NUMERIC_PREFIX_PATTERN = re.compile(r"^(\d+)")

MessageResolver = Callable[[str, str], str]


def _default_message(_key: str, default: str) -> str:
    return default


class DrawingPdfLibraryStorage:
    """Convenção de nome: `{codigo}.pdf`, `{base}.pdf`, `{base}_R{NN}.pdf`, `{base}-{N}.pdf`."""

    def __init__(
        self,
        base_dir: str | Path | None = None,
        *,
        message: MessageResolver | None = None,
    ) -> None:
        self.base_dir = Path(base_dir or settings.PC_DRAWING_PDF_LIBRARY_DIR)
        self._message = message or _default_message

    def resolve_pdf(self, code: str) -> DrawingFile:
        normalized = self._normalize_code(code)
        self._assert_library_available()

        path = self._find_pdf(normalized)
        if path is None:
            raise DrawingNotFound(
                self._message("drawingNotFound", "Desenho não encontrado para este PA.")
            )

        resolved = path.resolve()
        base = self.base_dir.resolve()
        if not str(resolved).startswith(str(base)) or not resolved.is_file():
            raise DrawingNotFound(
                self._message("drawingNotFound", "Desenho não encontrado para este PA.")
            )
        return DrawingFile(path=resolved, filename=resolved.name)

    def _normalize_code(self, code: str) -> str:
        normalized = str(code or "").strip().upper()
        invalid = self._message(
            "drawingCodeInvalid", "Código do PA inválido para busca de desenho."
        )
        if not normalized or ".." in normalized or "/" in normalized or "\\" in normalized:
            raise DrawingNotFound(invalid)
        if not _CODE_PATTERN.fullmatch(normalized):
            raise DrawingNotFound(invalid)
        return normalized

    def _assert_library_available(self) -> None:
        if not self.base_dir.is_dir():
            raise DrawingNotFound(
                self._message(
                    "drawingLibraryUnavailable",
                    "Biblioteca de desenhos indisponível: pasta não montada no servidor.",
                )
            )
        try:
            next(self.base_dir.iterdir())
        except StopIteration:
            raise DrawingNotFound(
                self._message(
                    "drawingLibraryEmpty",
                    "A pasta de desenhos está vazia no servidor. "
                    "Monte o compartilhamento do FILESERVER e recrie o serviço.",
                )
            ) from None
        except OSError:
            raise DrawingNotFound(
                self._message(
                    "drawingLibraryUnreadable",
                    "Não foi possível ler a pasta de desenhos no servidor.",
                )
            ) from None

    def _find_pdf(self, code: str) -> Path | None:
        exact = self.base_dir / f"{code}.pdf"
        if exact.is_file():
            return exact

        numeric_prefix = self._numeric_prefix(code)
        if not numeric_prefix:
            return None

        candidates = [
            path
            for path in self.base_dir.glob(f"{numeric_prefix}*.pdf")
            if path.is_file() and self._stem_matches(path.stem.upper(), code, numeric_prefix)
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda item: self._rank(item, code, numeric_prefix))

    def _stem_matches(self, stem: str, code: str, numeric_prefix: str) -> bool:
        if stem in {code, numeric_prefix}:
            return True
        if stem.startswith(numeric_prefix) and _REVISION_SUFFIX_PATTERN.search(stem):
            return True
        if stem.startswith(f"{numeric_prefix}-") and stem[len(numeric_prefix) + 1 :].isdigit():
            return True
        return False

    def _rank(self, path: Path, code: str, numeric_prefix: str) -> tuple[int, int, int]:
        stem = path.stem.upper()
        if stem == code:
            return (0, 0, 0)
        if stem == numeric_prefix:
            return (1, 0, 0)

        revision_match = _REVISION_SUFFIX_PATTERN.search(stem)
        if revision_match:
            return (2, -int(revision_match.group(1)), 0)

        variant_match = re.fullmatch(rf"{re.escape(numeric_prefix)}-(\d+)", stem)
        if variant_match:
            return (3, int(variant_match.group(1)), 0)
        return (9, 0, 0)

    def _numeric_prefix(self, code: str) -> str | None:
        match = _NUMERIC_PREFIX_PATTERN.match(code)
        return match.group(1) if match else None
