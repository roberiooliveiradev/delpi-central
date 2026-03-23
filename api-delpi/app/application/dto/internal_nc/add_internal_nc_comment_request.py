# app/application/dto/internal_nc/add_internal_nc_comment_request.py
from dataclasses import dataclass

@dataclass(slots=True)
class AddInternalNcCommentRequest:
    nonconformity_id: str
    comment_type: str
    content: str
    is_internal: bool
    created_by_user_id: str