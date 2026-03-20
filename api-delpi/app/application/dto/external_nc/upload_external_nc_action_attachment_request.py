# app/application/dto/external_nc/upload_external_nc_action_attachment_request.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class UploadExternalNcActionAttachmentRequest:
    action_id: str
    file_name: str
    original_name: str
    mime_type: Optional[str]
    size_bytes: int
    storage_provider: str
    storage_path: str
    checksum: Optional[str]
    uploaded_by_user_id: str