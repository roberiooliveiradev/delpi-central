from __future__ import annotations

from production_control_app.application.services.machine_load_service import MachineLoadService
from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.domain.errors import DrawingNotFound
from production_control_app.domain.ports.drawing_library import DrawingLibraryPort
from production_control_app.domain.product_drawing_pdf import DrawingFile


class PublicMachineLoadDrawingService:
    """PDF do desenho do PA para o cockpit — só se o código estiver na fila publicada."""

    def __init__(
        self,
        *,
        access: PublicCockpitAccessService,
        machine_load: MachineLoadService,
        drawings: DrawingLibraryPort,
    ) -> None:
        self._access = access
        self._machine_load = machine_load
        self._drawings = drawings

    def open_pdf(self, *, token: str, branch: str, pa_code: str) -> DrawingFile:
        if not self._access.is_valid_token(token):
            raise DrawingNotFound(
                self._access.message("invalidToken", "Link do cockpit inválido ou desativado.")
            )
        wanted = str(pa_code or "").strip()
        if not wanted:
            raise DrawingNotFound(
                self._access.message("paCodeRequired", "Informe o código do PA.")
            )
        if not self._machine_load.public_snapshot_contains_pa(branch=branch, pa_code=wanted):
            raise DrawingNotFound(
                self._access.message(
                    "paNotInPublishedQueue",
                    "Este PA não está na fila publicada desta filial.",
                )
            )
        try:
            return self._drawings.resolve_pdf(wanted)
        except DrawingNotFound as exc:
            detail = str(exc).strip()
            fallback = self._access.message(
                "drawingNotFound",
                "Desenho não encontrado para este PA.",
            )
            raise DrawingNotFound(detail or fallback) from None
