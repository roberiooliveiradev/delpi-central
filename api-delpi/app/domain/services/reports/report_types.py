"""Tipos de domínio — Delpi Reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class ReportAttachment:
    """Anexo para Microsoft Graph ``fileAttachment``."""

    name: str
    content_type: str
    content_base64: str
    is_inline: bool = False
    content_id: str | None = None


@dataclass(frozen=True, slots=True)
class ReportDataset:
    """Resultado tabular de um provider (pré-render)."""

    provider_key: str
    title: str
    columns: Sequence[str]
    rows: Sequence[Mapping[str, Any]]
    meta: Mapping[str, Any] = field(default_factory=dict)

    @property
    def row_count(self) -> int:
        return len(self.rows)


@dataclass(frozen=True, slots=True)
class EmailPayload:
    """Corpo de e-mail pronto para envio via Graph."""

    subject: str
    html_body: str
    attachments: Sequence[ReportAttachment] = field(default_factory=tuple)
