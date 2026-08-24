from __future__ import annotations

from production_control_app.application.services.delivery_map_service import DeliveryMapService
from production_control_app.application.services.delivery_map_settings import delivery_map_message
from production_control_app.application.services.public_delivery_map_access_service import (
    PublicDeliveryMapAccessService,
)
from production_control_app.core.security import PC_DELIVERY_MAP_VIEW, can
from production_control_app.domain.errors import DrawingNotFound
from production_control_app.domain.ports.drawing_library import DrawingLibraryPort
from production_control_app.domain.product_drawing_pdf import DrawingFile
from production_control_app.domain.services.branch_access_service import BranchAccessService


class DeliveryMapDrawingService:
    """PDF do desenho do PA — somente se o código estiver no snapshot do mapa de entrega."""

    def __init__(
        self,
        *,
        delivery_map: DeliveryMapService,
        branch_access: BranchAccessService,
        access: PublicDeliveryMapAccessService,
        drawings: DrawingLibraryPort,
    ) -> None:
        self._delivery_map = delivery_map
        self._branch_access = branch_access
        self._access = access
        self._drawings = drawings

    def open_pdf_for_user(
        self,
        user: object | None,
        *,
        branch: str,
        pa_code: str,
    ) -> DrawingFile:
        if not can(user, PC_DELIVERY_MAP_VIEW):
            raise PermissionError("Você não tem permissão para ver o mapa de entrega.")
        code = self._branch_access.assert_valid_branch(branch)
        self._branch_access.assert_can_view_branch(user, code)
        return self._open_pdf(
            branch=code,
            pa_code=pa_code,
            not_in_snapshot=delivery_map_message(
                "paNotInMap",
                "Este PA não está no mapa de entrega congelado desta filial.",
            ),
        )

    def open_pdf_public(
        self,
        *,
        token: str,
        branch: str,
        pa_code: str,
    ) -> DrawingFile:
        if not self._access.is_valid_token(token):
            raise DrawingNotFound(
                self._access.message("invalidToken", "Link do mapa de entrega inválido ou desativado.")
            )
        code = self._branch_access.assert_valid_branch(branch)
        return self._open_pdf(
            branch=code,
            pa_code=pa_code,
            not_in_snapshot=self._access.message(
                "paNotInMap",
                "Este PA não está no mapa de entrega congelado desta filial.",
            ),
        )

    def _open_pdf(self, *, branch: str, pa_code: str, not_in_snapshot: str) -> DrawingFile:
        wanted = str(pa_code or "").strip()
        if not wanted:
            raise DrawingNotFound(
                delivery_map_message("paCodeRequired", "Informe o código do PA.")
            )
        if not self._delivery_map.snapshot_contains_product(branch=branch, product_code=wanted):
            raise DrawingNotFound(not_in_snapshot)
        try:
            return self._drawings.resolve_pdf(wanted)
        except DrawingNotFound as exc:
            detail = str(exc).strip()
            fallback = delivery_map_message(
                "drawingNotFound",
                "Desenho não encontrado para este PA.",
            )
            raise DrawingNotFound(detail or fallback) from None
