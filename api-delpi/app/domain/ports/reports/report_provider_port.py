"""Port — contrato de provider de relatório (Delpi Reports)."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

from app.domain.services.reports.report_types import EmailPayload, ReportDataset


@runtime_checkable
class ReportProviderPort(Protocol):
    """Cada tipo de relatório implementa collect + render_email."""

    @property
    def key(self) -> str:
        """Identificador estável (ex.: safety_stock_shortage_30d)."""
        ...

    def describe_params(self) -> Mapping[str, Any]:
        """Schema declarativo dos parâmetros aceitos pelo provider."""
        ...

    def collect(
        self,
        params: Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
    ) -> ReportDataset:
        """Coleta dados do domínio (api-delpi / TOTVS) sem conhecer e-mail."""
        ...

    def render_email(self, dataset: ReportDataset) -> EmailPayload:
        """Monta subject/HTML/anexos a partir do dataset."""
        ...
