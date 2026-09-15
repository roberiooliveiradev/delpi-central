from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


GLB_MEDIA_TYPE = "model/gltf-binary"
GLB_MAGIC = b"glTF"


@dataclass(frozen=True)
class Product3DModel:
    product_code: str
    original_filename: str
    stored_filename: str
    content_type: str
    byte_size: int
    uploaded_by: str | None
    uploaded_at: datetime | None


@dataclass(frozen=True)
class Product3DModelFile:
    path: Path
    filename: str
    media_type: str = GLB_MEDIA_TYPE
