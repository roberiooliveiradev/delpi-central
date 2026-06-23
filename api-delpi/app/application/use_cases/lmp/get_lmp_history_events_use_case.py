from app.application.dto.lmp.get_lmp_history_request import GetLmpHistoryRequest
from app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort
from app.domain.services.lmp_history_event_enrichment import enrich_history_events


class GetLmpHistoryEventsUseCase:

    def __init__(self, repository: LMPQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: GetLmpHistoryRequest) -> dict:
        panel_context = self._repository.get_lmp_history_panel_context(request)
        events = self._repository.get_lmp_history_events(request)
        items = enrich_history_events(
            [event.to_dict() for event in events],
            reference_revision=panel_context.get("reference_revision"),
        )

        return {
            "sale_number": request.sale_number,
            "branch": panel_context.get("branch") or request.branch,
            "reference_revision": panel_context.get("reference_revision"),
            "panel_start_date": panel_context.get("panel_start_date"),
            "items": items,
            "total": len(items),
        }
