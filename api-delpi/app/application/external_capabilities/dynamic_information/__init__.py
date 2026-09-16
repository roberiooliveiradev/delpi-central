"""Provider-neutral dynamic governed READ over API DELPI technical actions."""

from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.execute_service import (
    execute_delpi_information,
)

__all__ = [
    "discover_delpi_information",
    "execute_delpi_information",
]
