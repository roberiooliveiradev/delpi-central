"""Port for the narrow BPMN Modeler lookups needed by the G5 integration.

The adapter is an HTTP client of the *public* BPMN Modeler API and forwards the
end-user bearer token (user-parity — no service credential, no owner bypass).
Application/domain code must not import httpx/requests.

State semantics (limited enum — no information leak):
- ``ok``: payload is the remote resource.
- ``not_found``: model/revision does not exist OR is not accessible to the
  current user (the Modeler deliberately answers 404 for foreign models).
- ``unauthorized``: the forwarded identity itself was rejected (session).
- ``unavailable``: network error, timeout or 5xx — dependency down.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

BpmnLookupState = Literal["ok", "not_found", "unauthorized", "unavailable"]


@dataclass(frozen=True)
class BpmnLookupResult:
    state: BpmnLookupState
    payload: Any = None

    @property
    def ok(self) -> bool:
        return self.state == "ok"


class BpmnModelerPort(Protocol):
    def list_models(self, *, authorization: str) -> BpmnLookupResult:
        """GET /models — models visible to the current user (picker metadata)."""
        ...

    def get_model(self, *, authorization: str, model_id: str) -> BpmnLookupResult:
        """GET /models/{model_id} — summary incl. latest_revision_number."""
        ...

    def list_revisions(self, *, authorization: str, model_id: str) -> BpmnLookupResult:
        """GET /models/{model_id}/revisions — picker metadata only."""
        ...

    def get_revision(
        self,
        *,
        authorization: str,
        model_id: str,
        revision_number: int,
    ) -> BpmnLookupResult:
        """GET /models/{model_id}/revisions/{revision_number} — summary."""
        ...
