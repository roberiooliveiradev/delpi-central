from app.application.dto.lmp.get_lmp_history_request import GetLmpHistoryRequest
from app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort
from app.domain.services.lmp_history_event_enrichment import (
    resolve_process_label,
    resolve_stage_label,
)
from app.domain.services.lmp_history_flow_transition import enrich_flow_transition_fields


class GetLmpHistoryFlowUseCase:

    def __init__(self, repository: LMPQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: GetLmpHistoryRequest) -> dict:
        panel_context = self._repository.get_lmp_history_panel_context(request)
        flow_events = self._repository.get_lmp_history_flow(request)
        items = [
            self._serialize_flow_event(event.to_dict())
            for event in flow_events
        ]

        return {
            "sale_number": request.sale_number,
            "branch": panel_context.get("branch") or request.branch,
            "reference_revision": panel_context.get("reference_revision"),
            "panel_start_date": panel_context.get("panel_start_date"),
            "items": items,
            "total": len(items),
        }

    @staticmethod
    def _serialize_flow_event(event: dict) -> dict:
        enriched = enrich_flow_transition_fields(event)
        return {
            **enriched,
            "process_label": resolve_process_label(event),
            "stage_label": resolve_stage_label(event),
        }
