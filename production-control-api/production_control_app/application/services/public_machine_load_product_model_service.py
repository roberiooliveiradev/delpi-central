from __future__ import annotations

import logging
from typing import Any

from production_control_app.application.services.machine_load_service import MachineLoadService
from production_control_app.application.services.product_3d_model_service import Product3DModelService
from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.domain.errors import Product3DModelNotFound
from production_control_app.domain.product_3d_model import Product3DModelFile
from production_control_app.domain.product_3d_model_code import normalize_product_code

logger = logging.getLogger("production_control.product_3d_models")


class PublicMachineLoadProductModelService:
    """GLB do produto da OP para o cockpit — só se o código estiver na fila publicada."""

    def __init__(
        self,
        *,
        access: PublicCockpitAccessService,
        machine_load: MachineLoadService,
        models: Product3DModelService,
    ) -> None:
        self._access = access
        self._machine_load = machine_load
        self._models = models

    def open_glb(self, *, token: str, branch: str, product_code: str) -> Product3DModelFile:
        if not self._access.is_valid_token(token):
            raise Product3DModelNotFound(
                self._access.message("invalidToken", "Link do cockpit inválido ou desativado.")
            )
        try:
            wanted = normalize_product_code(product_code)
        except Exception:
            raise Product3DModelNotFound(
                self._access.message("productCodeRequired", "Informe o código do produto.")
            ) from None
        if not self._machine_load.public_snapshot_contains_product(
            branch=branch, product_code=wanted
        ):
            raise Product3DModelNotFound(
                self._access.message(
                    "productNotInPublishedQueue",
                    "Este produto não está na fila publicada desta filial.",
                )
            )
        record = self._models.get_record(product_code=wanted)
        if record is None:
            raise Product3DModelNotFound(
                self._access.message(
                    "productModelNotFound",
                    "Modelo 3D não encontrado para este produto.",
                )
            )
        return self._models.open_stored_file(stored_filename=record.stored_filename)

    def annotate_public_queue(self, payload: dict[str, Any]) -> dict[str, Any]:
        selected = payload.get("selected")
        if not isinstance(selected, dict):
            return payload
        items = selected.get("items")
        if not isinstance(items, list):
            return payload
        codes = {
            str(item.get("product_code") or "").strip()
            for item in items
            if isinstance(item, dict)
        }
        try:
            existing = {code.upper() for code in self._models.existing_codes(codes)}
        except Exception:
            logger.exception("product_3d_model_annotate_failed")
            existing = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            code = str(item.get("product_code") or "").strip()
            item["has_3d_model"] = bool(code) and code.upper() in existing
        return payload
