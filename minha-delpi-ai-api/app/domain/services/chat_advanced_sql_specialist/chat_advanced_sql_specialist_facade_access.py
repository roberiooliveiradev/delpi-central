"""Acesso lazy à fachada — especialista SQL avançado."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.chat_advanced_sql_specialist_service import (
        ChatAdvancedSqlSpecialistService,
    )


def sql_specialist_service() -> type[ChatAdvancedSqlSpecialistService]:
    from app.domain.services.chat_advanced_sql_specialist_service import (
        ChatAdvancedSqlSpecialistService,
    )

    return ChatAdvancedSqlSpecialistService
