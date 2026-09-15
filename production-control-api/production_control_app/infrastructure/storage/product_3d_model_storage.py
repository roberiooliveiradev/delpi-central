"""Bytes do .glb no volume persistente do Portal PCP."""

from __future__ import annotations

from pathlib import Path

from production_control_app.config import settings
from production_control_app.domain.errors import Product3DModelNotFound
from production_control_app.domain.product_3d_model_code import normalize_product_code


class Product3DModelFilesystemStorage:
    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir or settings.PC_PRODUCT_3D_MODELS_DIR)

    def write_glb(self, *, product_code: str, payload: bytes) -> str:
        code = normalize_product_code(product_code)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{code}.glb"
        path = self._safe_path(filename)
        path.write_bytes(payload)
        return filename

    def resolve_glb(self, *, stored_filename: str) -> str:
        path = self._safe_path(stored_filename)
        if not path.is_file():
            raise Product3DModelNotFound("Modelo 3D não encontrado para este produto.")
        return str(path)

    def delete_glb(self, *, stored_filename: str) -> None:
        path = self._safe_path(stored_filename)
        if path.is_file():
            path.unlink()

    def _safe_path(self, stored_filename: str) -> Path:
        name = Path(str(stored_filename or "").strip()).name
        if not name or name != stored_filename or ".." in name:
            raise Product3DModelNotFound("Modelo 3D não encontrado para este produto.")
        if not name.endswith(".glb"):
            raise Product3DModelNotFound("Modelo 3D não encontrado para este produto.")
        resolved = (self.base_dir / name).resolve()
        base = self.base_dir.resolve()
        if not str(resolved).startswith(str(base)):
            raise Product3DModelNotFound("Modelo 3D não encontrado para este produto.")
        return resolved
