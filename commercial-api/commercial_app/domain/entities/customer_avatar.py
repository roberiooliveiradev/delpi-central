from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CustomerAvatarRecord:
    customer_code: str
    customer_store: str
    file_name: str
    content_type: str
    storage_key: str
    byte_size: int | None = None
