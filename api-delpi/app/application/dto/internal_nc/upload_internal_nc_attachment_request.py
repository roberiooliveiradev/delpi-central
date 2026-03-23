from dataclasses import dataclass
from typing import Optional

@dataclass(slots=True)
class UploadInternalNcAttachmentRequest:
    nonconformity_id: str
    file_name: str
    original_name: str
    mime_type: Optional[str]
    size_bytes: int
    storage_provider: str
    storage_path: str
    checksum: Optional[str]
    uploaded_by_user_id: str