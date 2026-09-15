from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from production_control_app.config import settings
from production_control_app.core.security import PC_PRODUCT_3D_MODELS_MANAGE, can
from production_control_app.domain.errors import Product3DModelInvalid, Product3DModelNotFound
from production_control_app.domain.ports.product_3d_model_repository import (
    Product3DModelRepositoryPort,
)
from production_control_app.domain.ports.product_3d_model_storage import Product3DModelStoragePort
from production_control_app.domain.product_3d_model import (
    GLB_MAGIC,
    GLB_MEDIA_TYPE,
    Product3DModel,
    Product3DModelFile,
)
from production_control_app.domain.product_3d_model_code import normalize_product_code

logger = logging.getLogger("production_control.product_3d_models")

_MAX_ORIGINAL_FILENAME = 255


def _user_label(user: object | None) -> str | None:
    if user is None:
        return None
    for attr in ("id", "username", "email", "preferred_username"):
        value = getattr(user, attr, None)
        if value:
            return str(value)[:120]
    return None


def _safe_original_filename(name: str | None) -> str:
    raw = Path(str(name or "").strip()).name
    if not raw:
        return "model.glb"
    return raw[:_MAX_ORIGINAL_FILENAME]


def _validate_glb_payload(payload: bytes, *, max_bytes: int) -> None:
    if not payload:
        raise Product3DModelInvalid("Envie um arquivo .glb.")
    if len(payload) > max_bytes:
        raise Product3DModelInvalid(
            f"O modelo 3D ultrapassa o tamanho máximo de {max_bytes // (1024 * 1024)} MB."
        )
    if not payload.startswith(GLB_MAGIC):
        raise Product3DModelInvalid("O arquivo precisa ser um modelo 3D no formato .glb.")


class Product3DModelService:
    """Anexa, lista e remove o .glb vigente do produto da OP."""

    def __init__(
        self,
        *,
        models: Product3DModelRepositoryPort,
        storage: Product3DModelStoragePort,
        max_bytes: int | None = None,
    ) -> None:
        self._models = models
        self._storage = storage
        self._max_bytes = int(max_bytes or settings.PC_PRODUCT_3D_MAX_BYTES)

    def list(self, user: object | None, *, search: str | None = None) -> dict[str, Any]:
        self._assert_manage(user)
        items = [self._to_payload(item) for item in self._models.list(search=search)]
        return {"items": items, "total": len(items)}

    def get(self, user: object | None, *, product_code: str) -> dict[str, Any]:
        self._assert_manage(user)
        model = self._models.get(product_code=normalize_product_code(product_code))
        if model is None:
            raise Product3DModelNotFound("Modelo 3D não encontrado para este produto.")
        return self._to_payload(model)

    def upsert(
        self,
        user: object | None,
        *,
        product_code: str,
        original_filename: str | None,
        payload: bytes,
    ) -> dict[str, Any]:
        self._assert_manage(user)
        code = normalize_product_code(product_code)
        filename = _safe_original_filename(original_filename)
        if not filename.lower().endswith(".glb"):
            raise Product3DModelInvalid("Envie um arquivo com extensão .glb.")
        _validate_glb_payload(payload, max_bytes=self._max_bytes)

        stored_filename = self._storage.write_glb(product_code=code, payload=payload)
        saved = self._models.upsert(
            Product3DModel(
                product_code=code,
                original_filename=filename,
                stored_filename=stored_filename,
                content_type=GLB_MEDIA_TYPE,
                byte_size=len(payload),
                uploaded_by=_user_label(user),
                uploaded_at=datetime.now(timezone.utc),
            )
        )
        logger.info(
            "product_3d_model_upserted",
            extra={
                "product_code": code,
                "byte_size": saved.byte_size,
                "uploaded_by": saved.uploaded_by,
            },
        )
        return self._to_payload(saved)

    def delete(self, user: object | None, *, product_code: str) -> dict[str, Any]:
        self._assert_manage(user)
        code = normalize_product_code(product_code)
        removed = self._models.delete(product_code=code)
        if removed is None:
            raise Product3DModelNotFound("Modelo 3D não encontrado para este produto.")
        self._storage.delete_glb(stored_filename=removed.stored_filename)
        logger.info(
            "product_3d_model_deleted",
            extra={"product_code": code, "uploaded_by": _user_label(user)},
        )
        return self._to_payload(removed)

    def existing_codes(self, codes: set[str]) -> set[str]:
        return self._models.existing_codes(codes)

    def get_record(self, *, product_code: str) -> Product3DModel | None:
        return self._models.get(product_code=product_code)

    def open_stored_file(self, *, stored_filename: str) -> Product3DModelFile:
        path = Path(self._storage.resolve_glb(stored_filename=stored_filename))
        return Product3DModelFile(path=path, filename=path.name, media_type=GLB_MEDIA_TYPE)

    @staticmethod
    def _assert_manage(user: object | None) -> None:
        if not can(user, PC_PRODUCT_3D_MODELS_MANAGE):
            raise PermissionError("Você não tem permissão para gerenciar modelos 3D de produto.")

    @staticmethod
    def _to_payload(model: Product3DModel) -> dict[str, Any]:
        uploaded_at = model.uploaded_at
        if isinstance(uploaded_at, datetime):
            stamp = uploaded_at.isoformat()
        else:
            stamp = None
        return {
            "product_code": model.product_code,
            "original_filename": model.original_filename,
            "byte_size": model.byte_size,
            "content_type": model.content_type,
            "uploaded_by": model.uploaded_by,
            "uploaded_at": stamp,
        }
