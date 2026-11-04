"""Configuração de runtime do publicador (env / defaults)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PublisherConfig:
    normalized_root: Path
    state_dir: Path
    api_base_url: str
    service_token: str
    caller_app: str
    timeout_seconds: float
    max_attempts: int
    stability_wait_seconds: float
    branch: str = "02"

    @classmethod
    def from_env(cls) -> PublisherConfig:
        token = (os.getenv("API_DELPI_INTERNAL_SERVICE_TOKEN") or "").strip()
        if not token:
            raise ValueError(
                "API_DELPI_INTERNAL_SERVICE_TOKEN ausente — credencial S2S obrigatória."
            )
        root = Path(
            os.getenv(
                "MYWEG_NORMALIZED_ROOT",
                "/home/michael/.local/share/MyWEG-Automacao/normalizados",
            )
        ).expanduser()
        state_dir = Path(
            os.getenv(
                "MYWEG_PUBLISHER_STATE_DIR",
                str(root.parent / "publisher-state"),
            )
        ).expanduser()
        api_base = (
            os.getenv("MYWEG_PC_API_URL")
            or os.getenv("PRODUCTION_CONTROL_API_URL")
            or "http://production-control-api:8000"
        ).rstrip("/")
        return cls(
            normalized_root=root,
            state_dir=state_dir,
            api_base_url=api_base,
            service_token=token,
            caller_app=(
                os.getenv("MYWEG_PUBLISHER_CALLER_APP") or "myweg-needs-publisher"
            ).strip(),
            timeout_seconds=float(os.getenv("MYWEG_PUBLISHER_TIMEOUT_SECONDS") or "60"),
            max_attempts=int(os.getenv("MYWEG_PUBLISHER_MAX_ATTEMPTS") or "3"),
            stability_wait_seconds=float(
                os.getenv("MYWEG_PUBLISHER_STABILITY_WAIT_SECONDS") or "0.75"
            ),
        )
