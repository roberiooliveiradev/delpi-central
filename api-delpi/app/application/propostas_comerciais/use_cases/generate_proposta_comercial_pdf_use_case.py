from __future__ import annotations

import re

from app.application.propostas_comerciais.use_cases.get_proposta_comercial_use_case import (
    GetPropostaComercialUseCase,
)
from app.domain.propostas_comerciais.ports.proposta_comercial_pdf_renderer_port import (
    PropostaComercialPdfRendererPort,
)


class GeneratePropostaComercialPdfUseCase:
    def __init__(
        self,
        get_proposta_comercial_use_case: GetPropostaComercialUseCase,
        pdf_renderer: PropostaComercialPdfRendererPort,
    ):
        self._get_proposta_comercial_use_case = get_proposta_comercial_use_case
        self._pdf_renderer = pdf_renderer

    def execute(
        self,
        proposta_interna: str,
        overrides: dict | None = None,
    ) -> tuple[bytes, str]:
        from app.domain.propostas_comerciais.services.proposta_comercial_pdf_export_overrides_service import (
            PropostaComercialPdfExportOverridesService,
        )

        detail = self._get_proposta_comercial_use_case.execute(proposta_interna)
        detail = PropostaComercialPdfExportOverridesService.apply(detail, overrides)
        pdf_bytes = self._pdf_renderer.render(detail)
        filename = self._build_filename(detail)
        return pdf_bytes, filename

    @staticmethod
    def _build_filename(detail: dict) -> str:
        cabecalho = detail.get("cabecalho") or {}
        numero_ov = str(cabecalho.get("numero_ov") or cabecalho.get("proposta_interna") or "proposta")
        safe = re.sub(r"[^A-Za-z0-9._-]+", "-", numero_ov).strip("-") or "proposta"
        return f"proposta-{safe}.pdf"
