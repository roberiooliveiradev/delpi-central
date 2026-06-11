from __future__ import annotations

from app.application.services.chat_presentation_column_label_discovery_service import (
    ChatPresentationColumnLabelDiscoveryService,
)
from app.domain.ports.presentation_column_label_discovery_port import (
    PresentationColumnLabelDiscoveryPort,
)


class InfrastructurePresentationColumnLabelDiscoveryAdapter(
    PresentationColumnLabelDiscoveryPort,
):
    def resolve_labels(
        self,
        keys: list[str],
        *,
        path: str = "",
        schema_labels: dict[str, str] | None = None,
        profile_labels: dict[str, str] | None = None,
        fields: dict[str, str] | None = None,
    ) -> dict[str, str]:
        return ChatPresentationColumnLabelDiscoveryService.resolve_labels(
            keys,
            path=path,
            schema_labels=schema_labels,
            profile_labels=profile_labels,
            fields=fields,
        )
