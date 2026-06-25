"""Acesso lazy à fachada — parâmetros operacionais."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.chat_operational_parameter_service import (
        ChatOperationalParameterService,
    )


def operational_parameter_service() -> type[ChatOperationalParameterService]:
    from app.domain.services.chat_operational_parameter_service import (
        ChatOperationalParameterService,
    )

    return ChatOperationalParameterService
