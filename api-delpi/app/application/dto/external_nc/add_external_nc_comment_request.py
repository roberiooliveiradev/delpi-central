# app/application/dto/external_nc/add_external_nc_comment_request.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AddExternalNcCommentRequest:
    nonconformity_id: str
    comment_type: str
    content: str
    is_internal: bool
    created_by_user_id: str