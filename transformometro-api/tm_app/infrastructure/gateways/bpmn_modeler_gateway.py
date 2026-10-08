"""HTTP adapter to the public BPMN Modeler API (G5 — user-delegated reads).

Forwards the end-user ``Authorization`` header verbatim: the BPMN Modeler keeps
enforcing its own ownership/RBAC, so a foreign model still resolves as 404.
No service token, no S2S credential, no artifact payloads are consumed here —
only the metadata needed to validate/select a (model_id, revision_number).
"""

from __future__ import annotations

import logging
import os

import httpx

from tm_app.application.ports.bpmn_modeler_port import BpmnLookupResult

logger = logging.getLogger(__name__)


def _base_url() -> str:
    return (
        os.getenv("BPMN_MODELER_API_BASE_URL") or "http://bpmn-modeler-api:8000"
    ).rstrip("/")


def _timeout_seconds() -> float:
    raw = os.getenv("BPMN_MODELER_API_TIMEOUT", "8")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 8.0
    return max(1.0, min(value, 30.0))


class BpmnModelerGateway:
    """Fail-closed, user-delegated consumer of the BPMN Modeler public API."""

    def _get(self, path: str, authorization: str) -> BpmnLookupResult:
        if not authorization or not str(authorization).strip():
            return BpmnLookupResult("unauthorized")
        url = f"{_base_url()}{path}"
        timeout = httpx.Timeout(_timeout_seconds(), connect=_timeout_seconds())
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url, headers={"Authorization": authorization})
        except httpx.RequestError as exc:
            logger.warning(
                "bpmn_modeler_lookup_unavailable path=%s err=%s", path, exc
            )
            return BpmnLookupResult("unavailable")

        status = response.status_code
        if status == 200:
            return BpmnLookupResult("ok", response.json())
        if status == 404:
            return BpmnLookupResult("not_found")
        if status == 401:
            return BpmnLookupResult("unauthorized")
        if status == 403:
            # Foreign/inaccessible — never leak existence, mirror Modeler 404.
            return BpmnLookupResult("not_found")
        logger.warning(
            "bpmn_modeler_lookup_failed path=%s status=%s", path, status
        )
        return BpmnLookupResult("unavailable")

    def list_models(self, *, authorization: str) -> BpmnLookupResult:
        return self._get("/models", authorization)

    def get_model(self, *, authorization: str, model_id: str) -> BpmnLookupResult:
        return self._get(f"/models/{model_id}", authorization)

    def list_revisions(
        self, *, authorization: str, model_id: str
    ) -> BpmnLookupResult:
        return self._get(f"/models/{model_id}/revisions", authorization)

    def get_revision(
        self,
        *,
        authorization: str,
        model_id: str,
        revision_number: int,
    ) -> BpmnLookupResult:
        return self._get(
            f"/models/{model_id}/revisions/{revision_number}", authorization
        )
