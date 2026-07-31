"""Envelope paged_list genérico (page / total / pagination.is_complete).

Reexport canônico — preferir `app.application.services.paged_list_envelope_service`.
"""

from app.application.services.paged_list_envelope_service import (  # noqa: F401
    build_has_next_pagination,
    build_paged_list_envelope,
)
