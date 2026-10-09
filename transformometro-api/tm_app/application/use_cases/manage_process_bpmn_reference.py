"""Use cases for the process ↔ BPMN model explicit reference (G5).

Ownership: the reference row lives in the Transformômetro schema and stores
only the external identity (model_id, revision_number). Remote resolution is
user-delegated — the BPMN Modeler keeps enforcing ownership/RBAC.

Failure model:
- reads degrade: a stored reference survives Modeler unavailability;
- writes fail closed: link/replace is denied when the Modeler cannot
  validate the target (no dangling reference is persisted on write).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from tm_app.application.ports.bpmn_modeler_port import (
    BpmnLookupResult,
    BpmnModelerPort,
)
from tm_app.application.security.authorization_policy import (
    TransformometroAuthorizationPolicy,
)
from tm_app.domain.entities.process_bpmn_reference import ProcessBpmnReference
from tm_app.domain.ports.process_bpmn_reference_repository_port import (
    ProcessBpmnReferenceRepositoryPort,
)


class BpmnDependencyUnavailable(RuntimeError):
    """Modeler unreachable — writes must fail closed (503)."""

    status_code = 503


class DualModeConflict(RuntimeError):
    """XOR violation (G7/ADR-006) — o processo já possui documento nativo."""

    status_code = 409


def _data(payload: Any) -> dict[str, Any]:
    """Unwrap the shared ``{success, data}`` envelope when present."""
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"]
    return payload if isinstance(payload, dict) else {}


def _items(payload: Any) -> list[dict[str, Any]]:
    data = _data(payload)
    items = data.get("items")
    if isinstance(items, list):
        return [i for i in items if isinstance(i, dict)]
    if isinstance(payload, list):
        return [i for i in payload if isinstance(i, dict)]
    return []


def _normalize_uuid(value: str, label: str) -> str:
    raw = str(value or "").strip()
    try:
        return str(UUID(raw))
    except (ValueError, AttributeError, TypeError):
        raise ValueError(f"{label} inválido.") from None


def _model_id(model: dict[str, Any]) -> str:
    return str(model.get("id") or model.get("model_id") or "")


class ProcessBpmnReferenceUseCases:
    def __init__(
        self,
        repo: ProcessBpmnReferenceRepositoryPort,
        bpmn: BpmnModelerPort,
        policy: TransformometroAuthorizationPolicy | None = None,
        docs: Any | None = None,
    ) -> None:
        self._repo = repo
        self._bpmn = bpmn
        self._docs = docs
        self._policy = policy or TransformometroAuthorizationPolicy()

    # -- reads -----------------------------------------------------------

    def get_reference(
        self, user: Any, processo_id: str, *, authorization: str
    ) -> dict[str, Any]:
        self._policy.require_access(user)
        pid = self._require_processo(processo_id)
        ref = self._repo.get_active(pid)
        resolved = None
        if ref is not None:
            resolved = self.resolve_reference(ref, authorization=authorization)
        return {
            "reference": ref.to_dict() if ref else None,
            "resolved": resolved,
        }

    def list_model_candidates(
        self, user: Any, processo_id: str, *, authorization: str
    ) -> dict[str, Any]:
        """Models the current user can see — picker metadata only."""
        self._policy.require_access(user)
        self._require_processo(processo_id)
        result = self._bpmn.list_models(authorization=authorization)
        if result.state == "unauthorized":
            raise PermissionError("Sessão inválida ou expirada.")
        if result.state != "ok":
            raise BpmnDependencyUnavailable(
                "Modelo de processos BPMN temporariamente indisponível."
            )
        items = []
        for model in _items(result.payload):
            items.append(
                {
                    "model_id": _model_id(model),
                    "display_name": model.get("display_name"),
                    "latest_revision_number": model.get("latest_revision_number"),
                    "archived": bool(model.get("archived_at")),
                }
            )
        return {"state": "resolved", "items": items}

    def list_model_revisions(
        self, user: Any, processo_id: str, model_id: str, *, authorization: str
    ) -> dict[str, Any]:
        self._policy.require_access(user)
        self._require_processo(processo_id)
        mid = _normalize_uuid(model_id, "model_id")
        result = self._bpmn.list_revisions(authorization=authorization, model_id=mid)
        self._raise_for_lookup(result, "Modelo BPMN não encontrado ou sem acesso.")
        items = []
        for rev in _items(result.payload):
            items.append(
                {
                    "revision_number": rev.get("revision_number"),
                    "revision_id": rev.get("revision_id"),
                    "name": rev.get("name"),
                    "description": rev.get("description"),
                    "origin": rev.get("origin"),
                    "created_at": rev.get("created_at"),
                    "created_by_name": rev.get("created_by_name"),
                }
            )
        return {"state": "resolved", "model_id": mid, "items": items}

    # -- writes (fail closed) ---------------------------------------------

    def set_reference(
        self,
        user: Any,
        processo_id: str,
        *,
        model_id: str,
        revision_number: int,
        authorization: str,
    ) -> dict[str, Any]:
        self._policy.require_access(user)
        pid = self._require_processo(processo_id)
        if self._docs is not None and self._docs.has_active(pid):
            raise DualModeConflict(
                "O processo já possui um documento BPMN nativo; "
                "remova-o antes de vincular um modelo externo."
            )
        mid = _normalize_uuid(model_id, "model_id")
        rev_no = self._normalize_revision_number(revision_number)
        actor = str(getattr(user, "id", "") or getattr(user, "sub", "") or "")

        model_result = self._bpmn.get_model(authorization=authorization, model_id=mid)
        self._raise_for_lookup(
            model_result, "Modelo BPMN não encontrado ou sem acesso."
        )
        model = _data(model_result.payload)
        if model.get("latest_revision_number") in (None, 0):
            raise ValueError(
                "Este modelo ainda não possui uma revisão. "
                "Crie uma revisão no Modelador antes de vincular."
            )

        rev_result = self._bpmn.get_revision(
            authorization=authorization, model_id=mid, revision_number=rev_no
        )
        self._raise_for_lookup(
            rev_result, "Revisão BPMN não encontrada ou sem acesso."
        )

        current, previous = self._repo.upsert(
            processo_id=pid,
            bpmn_model_id=mid,
            bpmn_revision_number=rev_no,
            actor_user_id=actor,
        )
        return {
            "reference": current.to_dict(),
            "previous": previous.to_dict() if previous else None,
            "resolved": self.resolve_reference(current, authorization=authorization),
        }

    def remove_reference(
        self, user: Any, processo_id: str
    ) -> dict[str, Any]:
        self._policy.require_access(user)
        pid = self._require_processo(processo_id)
        actor = str(getattr(user, "id", "") or getattr(user, "sub", "") or "")
        removed = self._repo.soft_delete(processo_id=pid, actor_user_id=actor)
        if removed is None:
            raise LookupError("Nenhum modelo BPMN vinculado a este processo.")
        return {
            "removed": removed.to_dict(),
            "reference": None,
            "resolved": None,
        }

    # -- helpers ----------------------------------------------------------

    def resolve_reference(
        self, ref: ProcessBpmnReference, *, authorization: str
    ) -> dict[str, Any]:
        """DERIVED / REMOTE READ — never persisted, never mutates the link."""
        model_result = self._bpmn.get_model(
            authorization=authorization, model_id=ref.bpmn_model_id
        )
        if model_result.state == "unavailable":
            return {"state": "unavailable"}
        if model_result.state != "ok":
            return {"state": "inaccessible_or_missing"}
        model = _data(model_result.payload)
        rev_result = self._bpmn.get_revision(
            authorization=authorization,
            model_id=ref.bpmn_model_id,
            revision_number=ref.bpmn_revision_number,
        )
        if rev_result.state == "unavailable":
            return {"state": "unavailable"}
        if rev_result.state != "ok":
            return {"state": "inaccessible_or_missing"}
        rev = _data(rev_result.payload)
        return {
            "state": "resolved",
            "model_display_name": model.get("display_name"),
            "model_archived": bool(model.get("archived_at")),
            "latest_revision_number": model.get("latest_revision_number"),
            "revision_id": rev.get("revision_id"),
            "revision_name": rev.get("name"),
            "revision_description": rev.get("description"),
            "revision_created_at": rev.get("created_at"),
            "revision_created_by_name": rev.get("created_by_name"),
            "artifact_sha256": rev.get("artifact_sha256"),
        }

    def _require_processo(self, processo_id: str) -> str:
        pid = _normalize_uuid(processo_id, "processo_id")
        if not self._repo.process_exists(pid):
            raise LookupError("Processo não encontrado.")
        return pid

    @staticmethod
    def _normalize_revision_number(value: int) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            raise ValueError("revision_number inválido.") from None
        if number <= 0:
            raise ValueError("revision_number deve ser maior que zero.")
        return number

    @staticmethod
    def _raise_for_lookup(result: BpmnLookupResult, not_found_message: str) -> None:
        if result.state == "ok":
            return
        if result.state == "unauthorized":
            raise PermissionError("Sessão inválida ou expirada.")
        if result.state == "not_found":
            raise LookupError(not_found_message)
        raise BpmnDependencyUnavailable(
            "Modelo de processos BPMN temporariamente indisponível."
        )
