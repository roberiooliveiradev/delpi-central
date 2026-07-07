from __future__ import annotations

from cx_app.application.services.photo_storage import PhotoStorage
from cx_app.config import settings


class FormImageStorage(PhotoStorage):
    """Imagens de layout de formulários (fundo, ícones por página)."""

    def __init__(self) -> None:
        super().__init__(base_dir=settings.CX_FORM_IMAGE_UPLOAD_DIR)
