"""Configuração de runtime do publicador manual de NF MyWEG."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from production_control_app.jobs.myweg_invoice_observations_publisher import (
    DEFAULT_INVOICE_ROOT,
)


@dataclass(frozen=True)
class InvoicePublisherConfig:
    invoice_root: Path
    api_base_url: str
    service_token: str
    caller_app: str
    timeout_seconds: float
    max_attempts: int
    stability_wait_seconds: float
    branch: str = "02"

    @classmethod
    def from_env(cls) -> InvoicePublisherConfig:
        token = (os.getenv("API_DELPI_INTERNAL_SERVICE_TOKEN") or "").strip()
        if not token:
            raise ValueError(
                "API_DELPI_INTERNAL_SERVICE_TOKEN ausente — credencial S2S obrigatória."
            )
        root = Path(
            os.getenv("MYWEG_INVOICE_ROOT", DEFAULT_INVOICE_ROOT)
        ).expanduser()
        api_base = (
            os.getenv("MYWEG_PC_API_URL")
            or os.getenv("PRODUCTION_CONTROL_API_URL")
            or "http://production-control-api:8000"
        ).rstrip("/")
        return cls(
            invoice_root=root,
            api_base_url=api_base,
            service_token=token,
            caller_app=(
                os.getenv("MYWEG_INVOICE_PUBLISHER_CALLER_APP")
                or "myweg-invoice-observations-publisher"
            ).strip(),
            timeout_seconds=float(
                os.getenv("MYWEG_INVOICE_PUBLISHER_TIMEOUT_SECONDS") or "60"
            ),
            max_attempts=int(
                os.getenv("MYWEG_INVOICE_PUBLISHER_MAX_ATTEMPTS") or "3"
            ),
            stability_wait_seconds=float(
                os.getenv("MYWEG_INVOICE_PUBLISHER_STABILITY_WAIT_SECONDS") or "0.75"
            ),
        )
