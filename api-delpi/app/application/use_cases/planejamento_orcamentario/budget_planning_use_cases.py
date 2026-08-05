
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from app.domain.services.planejamento_orcamentario.acknowledgement_guard import (
    BudgetGuidanceAcknowledgementGuard,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetCostCenterConflictError,
    BudgetCostCenterInvalidError,
    BudgetCostCenterNotFoundError,
    BudgetDocumentNotFoundError,
    BudgetExerciseAlreadyActiveError,
    BudgetExerciseInvalidDatesError,
    BudgetExerciseInvalidTransitionError,
    BudgetExerciseNotFoundError,
    BudgetGuidanceAlreadyPublishedError,
    BudgetGuidanceImmutableError,
    BudgetGuidanceNotFoundError,
    BudgetGuidanceNotPublishedError,
    BudgetScopeConflictError,
    BudgetScopeNotFoundError,
    BudgetUserNotAuthorizedError,
)
from app.domain.services.planejamento_orcamentario.org_cost_center_constants import (
    BUDGET_BRANCH_UNIT_NAMES,
    COST_CENTER_SOURCE_ERP,
    COST_CENTER_SOURCE_MANUAL,
    normalize_budget_branch,
    serialize_org_cost_center,
)
from app.domain.services.planejamento_orcamentario.exercise_state_service import (
    assert_transition,
    modules_unlocked_for_exercise,
)
from app.application.services.planejamento_orcamentario.document_storage import (
    BudgetDocumentStorage,
)
from app.infrastructure.persistence.plugins.repositories.planejamento_orcamentario.postgres_budget_planning_repository import (
    PostgresBudgetPlanningRepository,
)
from app.infrastructure.persistence.totvs.financeiro_despesas_centro_custo.despesas_centro_custo_repository import (
    DespesasCentroCustoRepository,
)


@dataclass(frozen=True)
class BudgetActor:
    user_id: str
    user_name: str
    permissions: frozenset[str]


def _parse_date(value: Any, field: str) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, type(None)):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise BudgetExerciseInvalidDatesError(f"Data inválida em {field}.") from exc


def _validate_exercise_dates(
    preparation: date | None,
    filling: date | None,
    deadline: date | None,
    closed: date | None,
) -> None:
    if preparation and filling and preparation > filling:
        raise BudgetExerciseInvalidDatesError(
            "Data de preparação não pode ser posterior ao início do preenchimento."
        )
    if filling and deadline and filling > deadline:
        raise BudgetExerciseInvalidDatesError(
            "Início do preenchimento não pode ser posterior ao prazo."
        )
    if deadline and closed and deadline > closed:
        raise BudgetExerciseInvalidDatesError(
            "Prazo não pode ser posterior ao encerramento."
        )


def _public_document(doc: dict[str, Any]) -> dict[str, Any]:
    out = dict(doc)
    out.pop("storage_key", None)
    return out


class BudgetPlanningUseCases:
    def __init__(
        self,
        repository: PostgresBudgetPlanningRepository | None = None,
        storage: BudgetDocumentStorage | None = None,
        erp_cost_centers: DespesasCentroCustoRepository | None = None,
    ) -> None:
        self._repo = repository or PostgresBudgetPlanningRepository()
        self._storage = storage or BudgetDocumentStorage()
        self._erp = erp_cost_centers or DespesasCentroCustoRepository()
        self._guard = BudgetGuidanceAcknowledgementGuard(self._repo)

    # ---- context ----
    def get_context(self, actor: BudgetActor) -> dict[str, Any]:
        state = self._guard.evaluate(user_sub=actor.user_id)
        exercise = state.get("exercise")
        guidance = state.get("guidance")
        ack = state.get("acknowledgement")
        scopes = self._repo.list_scopes_for_user(actor.user_id)
        caps = {
            "access": "planejamento-orcamentario.access" in actor.permissions
            or "planejamento-orcamentario.admin" in actor.permissions,
            "guidance_view": bool(
                actor.permissions
                & {
                    "planejamento-orcamentario.guidance.view",
                    "planejamento-orcamentario.guidance.manage",
                    "planejamento-orcamentario.admin",
                    "planejamento-orcamentario.access",
                }
            ),
            "guidance_manage": bool(
                actor.permissions
                & {
                    "planejamento-orcamentario.guidance.manage",
                    "planejamento-orcamentario.admin",
                }
            ),
            "scopes_manage": bool(
                actor.permissions
                & {
                    "planejamento-orcamentario.scopes.manage",
                    "planejamento-orcamentario.admin",
                }
            ),
            "admin": "planejamento-orcamentario.admin" in actor.permissions,
        }
        return {
            "exercise": exercise,
            "guidance": {
                "current_version": guidance.get("version_number") if guidance else None,
                "guidance_id": guidance.get("id") if guidance else None,
                "title": guidance.get("title") if guidance else None,
                "acknowledged": bool(state.get("acknowledged")),
                "acknowledged_at": ack.get("acknowledged_at") if ack else None,
                "published_at": guidance.get("published_at") if guidance else None,
            },
            "scopes": scopes,
            "capabilities": caps,
            "modules_unlocked": bool(state.get("modules_unlocked")),
            "reason": state.get("reason"),
        }

    def assert_modules_unlocked(self, actor: BudgetActor) -> dict[str, Any]:
        return self._guard.assert_modules_unlocked(user_sub=actor.user_id)

    # ---- exercises admin ----
    def list_exercises(self) -> list[dict[str, Any]]:
        return self._repo.list_exercises()

    def get_exercise(self, exercise_id: str) -> dict[str, Any]:
        exercise = self._repo.get_exercise(exercise_id)
        if not exercise:
            raise BudgetExerciseNotFoundError("Exercício orçamentário não encontrado.")
        return exercise

    def create_exercise(self, actor: BudgetActor, body: dict[str, Any]) -> dict[str, Any]:
        year = int(body["year"])
        if self._repo.get_exercise_by_year(year):
            raise BudgetExerciseAlreadyActiveError(
                f"Já existe exercício para o ano {year}.",
                code="budget_exercise_already_active",
            )
        prep = _parse_date(body.get("preparation_starts_at"), "preparation_starts_at")
        filling = _parse_date(body.get("filling_starts_at"), "filling_starts_at")
        deadline = _parse_date(body.get("deadline_at"), "deadline_at")
        closed = _parse_date(body.get("closed_at"), "closed_at")
        _validate_exercise_dates(prep, filling, deadline, closed)
        created = self._repo.create_exercise(
            {
                "year": year,
                "name": str(body["name"]).strip(),
                "description": (body.get("description") or None),
                "status": "draft",
                "preparation_starts_at": prep,
                "filling_starts_at": filling,
                "deadline_at": deadline,
                "closed_at": closed,
                "is_active": False,
                "created_by_user_id": actor.user_id,
                "created_by_name": actor.user_name,
                "updated_by_user_id": actor.user_id,
                "updated_by_name": actor.user_name,
            }
        )
        self._repo.append_audit(
            exercise_id=created["id"],
            entity_type="budget_exercise",
            entity_id=created["id"],
            action="exercise.created",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=None,
            after_state=created,
        )
        # seed default org units for admin convenience (catalog, not TOTVS)
        self._repo.upsert_org_unit("01", "DELPI Jaraguá — Chicotes")
        self._repo.upsert_org_unit("02", "DELPI Espírito Santo")
        return created

    def update_exercise(
        self, actor: BudgetActor, exercise_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        current = self.get_exercise(exercise_id)
        if current["status"] not in {"draft", "open", "closing"} and any(
            k in body for k in ("name", "description", "preparation_starts_at", "filling_starts_at", "deadline_at")
        ):
            # allow limited edits; locked/archived only status transitions elsewhere
            if current["status"] in {"locked", "archived"}:
                raise BudgetExerciseInvalidTransitionError(
                    "Exercício bloqueado ou arquivado não pode ser editado.",
                )
        prep = _parse_date(body.get("preparation_starts_at", current.get("preparation_starts_at")), "preparation_starts_at")
        filling = _parse_date(body.get("filling_starts_at", current.get("filling_starts_at")), "filling_starts_at")
        deadline = _parse_date(body.get("deadline_at", current.get("deadline_at")), "deadline_at")
        closed = _parse_date(body.get("closed_at", current.get("closed_at")), "closed_at")
        _validate_exercise_dates(prep, filling, deadline, closed)
        fields: dict[str, Any] = {
            "updated_by_user_id": actor.user_id,
            "updated_by_name": actor.user_name,
        }
        for key in ("name", "description"):
            if key in body:
                fields[key] = body[key]
        fields["preparation_starts_at"] = prep
        fields["filling_starts_at"] = filling
        fields["deadline_at"] = deadline
        fields["closed_at"] = closed
        if "status" in body and body["status"] != current["status"]:
            target = str(body["status"])
            assert_transition(current["status"], target)
            fields["status"] = target
            if target == "open":
                self._repo.clear_other_active(exercise_id)
                fields["is_active"] = True
            if target in {"locked", "archived", "closing"} and target == "archived":
                fields["is_active"] = False
            if target == "locked":
                fields["is_active"] = False
        updated = self._repo.update_exercise(exercise_id, fields)
        self._repo.append_audit(
            exercise_id=exercise_id,
            entity_type="budget_exercise",
            entity_id=exercise_id,
            action="exercise.updated",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=current,
            after_state=updated,
        )
        return updated

    def transition_exercise(
        self, actor: BudgetActor, exercise_id: str, *, action: str, comment: str | None = None
    ) -> dict[str, Any]:
        mapping = {
            "publish": "open",
            "start_close": "closing",
            "lock": "locked",
            "reopen": "open",
            "archive": "archived",
        }
        if action not in mapping:
            raise BudgetExerciseInvalidTransitionError(
                f"Ação inválida: {action}.",
                status_code=422,
            )
        return self.update_exercise(actor, exercise_id, {"status": mapping[action]})

    # ---- guidance ----
    def _hydrate_guidance(self, guidance: dict[str, Any]) -> dict[str, Any]:
        gid = guidance["id"]
        return {
            **guidance,
            "premises": self._repo.list_premises(gid),
            "schedule": self._repo.list_schedule(gid),
        }

    def get_or_create_guidance_draft(self, actor: BudgetActor, exercise_id: str) -> dict[str, Any]:
        self.get_exercise(exercise_id)
        draft = self._repo.get_guidance_draft(exercise_id)
        if draft:
            return self._hydrate_guidance(draft)
        published = self._repo.get_current_published_guidance(exercise_id)
        base = {
            "exercise_id": exercise_id,
            "title": (published or {}).get("title") or "Orientações do Planejamento Orçamentário",
            "board_message": (published or {}).get("board_message") or "",
            "sender_name": (published or {}).get("sender_name"),
            "sender_role": (published or {}).get("sender_role"),
            "objective": (published or {}).get("objective") or "",
            "general_guidance": (published or {}).get("general_guidance") or "",
            "additional_notes": (published or {}).get("additional_notes") or "",
            "created_by_user_id": actor.user_id,
            "updated_by_user_id": actor.user_id,
        }
        draft = self._repo.create_guidance_draft(base)
        if published:
            self._repo.replace_premises(draft["id"], self._repo.list_premises(published["id"]))
            self._repo.replace_schedule(draft["id"], self._repo.list_schedule(published["id"]))
        self._repo.append_audit(
            exercise_id=exercise_id,
            entity_type="guidance_version",
            entity_id=draft["id"],
            action="guidance.draft_created",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=None,
            after_state=draft,
        )
        return self._hydrate_guidance(draft)

    def update_guidance_draft(
        self, actor: BudgetActor, guidance_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        current = self._repo.get_guidance(guidance_id)
        if not current:
            raise BudgetGuidanceNotFoundError("Orientações não encontradas.")
        if current["status"] != "draft":
            raise BudgetGuidanceImmutableError(
                "Versão publicada é imutável. Crie um novo rascunho para alterar."
            )
        fields = {k: body[k] for k in (
            "title", "board_message", "sender_name", "sender_role",
            "objective", "general_guidance", "additional_notes",
        ) if k in body}
        fields["updated_by_user_id"] = actor.user_id
        updated = self._repo.update_guidance_draft(guidance_id, fields)
        if "premises" in body:
            self._normalize_and_replace_premises(guidance_id, body["premises"])
        if "schedule" in body:
            self._normalize_and_replace_schedule(guidance_id, body["schedule"])
        result = self._hydrate_guidance(updated)
        self._repo.append_audit(
            exercise_id=current["exercise_id"],
            entity_type="guidance_version",
            entity_id=guidance_id,
            action="guidance.draft_updated",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=current,
            after_state=result,
        )
        return result

    def _normalize_and_replace_premises(self, guidance_id: str, premises: list[dict[str, Any]]) -> None:
        normalized = []
        for idx, item in enumerate(premises or []):
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            value_numeric = item.get("value_numeric")
            if value_numeric is not None and value_numeric != "":
                try:
                    value_numeric = str(Decimal(str(value_numeric)))
                except (InvalidOperation, ValueError) as exc:
                    raise BudgetExerciseInvalidDatesError(
                        f"Premissa inválida (valor numérico): {name}.",
                        code="budget_guidance_version_conflict",
                    ) from exc
            else:
                value_numeric = None
            value_text = item.get("value_text")
            if value_text is not None:
                value_text = str(value_text).strip() or None
            if value_text is None and value_numeric is None:
                raise BudgetExerciseInvalidDatesError(
                    f"Premissa '{name}' precisa de valor textual ou numérico.",
                    code="budget_guidance_version_conflict",
                )
            normalized.append({
                "name": name,
                "value_text": value_text,
                "value_numeric": value_numeric,
                "unit_label": (str(item["unit_label"]).strip() if item.get("unit_label") else None),
                "description": item.get("description"),
                "display_order": int(item.get("display_order", idx)),
                "active": bool(item.get("active", True)),
            })
        self._repo.replace_premises(guidance_id, normalized)

    def _normalize_and_replace_schedule(self, guidance_id: str, items: list[dict[str, Any]]) -> None:
        normalized = []
        for idx, item in enumerate(items or []):
            title = str(item.get("title") or "").strip()
            if not title:
                continue
            starts = _parse_date(item.get("starts_on"), "starts_on")
            ends = _parse_date(item.get("ends_on"), "ends_on")
            if not starts:
                raise BudgetExerciseInvalidDatesError("Item de cronograma exige data inicial.")
            if ends and ends < starts:
                raise BudgetExerciseInvalidDatesError(
                    "Data final do cronograma não pode ser anterior à inicial."
                )
            normalized.append({
                "title": title,
                "description": item.get("description"),
                "starts_on": starts,
                "ends_on": ends,
                "display_order": int(item.get("display_order", idx)),
                "highlighted": bool(item.get("highlighted", False)),
            })
        self._repo.replace_schedule(guidance_id, normalized)

    def publish_guidance(self, actor: BudgetActor, guidance_id: str) -> dict[str, Any]:
        current = self._repo.get_guidance(guidance_id)
        if not current:
            raise BudgetGuidanceNotFoundError("Orientações não encontradas.")
        if current["status"] == "published":
            raise BudgetGuidanceAlreadyPublishedError("Esta versão já está publicada.")
        if not str(current.get("title") or "").strip():
            raise BudgetGuidanceNotPublishedError("Título é obrigatório para publicar.")
        if not str(current.get("board_message") or "").strip():
            raise BudgetGuidanceNotPublishedError("Mensagem da Diretoria é obrigatória.")
        published = self._repo.publish_guidance(
            guidance_id, actor_id=actor.user_id, actor_name=actor.user_name
        )
        result = self._hydrate_guidance(published)
        self._repo.append_audit(
            exercise_id=current["exercise_id"],
            entity_type="guidance_version",
            entity_id=guidance_id,
            action="guidance.published",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=current,
            after_state=result,
        )
        return result

    def get_current_guidance_for_user(self, actor: BudgetActor) -> dict[str, Any]:
        exercise = self._repo.get_active_exercise()
        if not exercise:
            raise BudgetExerciseNotFoundError("Não há exercício ativo.")
        guidance = self._repo.get_current_published_guidance(exercise["id"])
        if not guidance:
            raise BudgetGuidanceNotPublishedError("Orientações ainda não publicadas.")
        hydrated = self._hydrate_guidance(guidance)
        ack = self._repo.get_acknowledgement(
            user_sub=actor.user_id, guidance_version_id=guidance["id"]
        )
        hydrated["acknowledged"] = ack is not None
        hydrated["acknowledged_at"] = ack.get("acknowledged_at") if ack else None
        hydrated["exercise"] = {
            "id": exercise["id"],
            "year": exercise["year"],
            "name": exercise["name"],
            "status": exercise["status"],
        }
        return hydrated

    def acknowledge_current_guidance(self, actor: BudgetActor, request_id: str | None = None) -> dict[str, Any]:
        exercise = self._repo.get_active_exercise()
        if not exercise:
            raise BudgetExerciseNotFoundError("Não há exercício ativo.")
        if not modules_unlocked_for_exercise(exercise["status"]) and exercise["status"] not in {"open", "closing"}:
            # allow ack while open/closing; also allow if draft? no - must be published guidance
            pass
        if exercise["status"] in {"draft", "archived"}:
            raise BudgetGuidanceNotPublishedError(
                "Exercício não está disponível para confirmação de leitura."
            )
        guidance = self._repo.get_current_published_guidance(exercise["id"])
        if not guidance:
            raise BudgetGuidanceNotPublishedError("Orientações ainda não publicadas.")
        existing = self._repo.get_acknowledgement(
            user_sub=actor.user_id, guidance_version_id=guidance["id"]
        )
        ack = self._repo.create_acknowledgement(
            {
                "exercise_id": exercise["id"],
                "guidance_version_id": guidance["id"],
                "user_sub": actor.user_id,
                "user_name": actor.user_name,
                "request_id": request_id,
            }
        )
        if not existing:
            self._repo.append_audit(
                exercise_id=exercise["id"],
                entity_type="reading_acknowledgement",
                entity_id=ack["id"],
                action="guidance.acknowledged",
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                before_state=None,
                after_state=ack,
            )
        return {
            "acknowledged": True,
            "acknowledged_at": ack["acknowledged_at"],
            "guidance_version": guidance["version_number"],
            "idempotent_replay": existing is not None,
            "modules_unlocked": modules_unlocked_for_exercise(exercise["status"]),
        }

    # ---- documents ----
    def list_current_documents(self, actor: BudgetActor) -> list[dict[str, Any]]:
        exercise = self._repo.get_active_exercise()
        if not exercise:
            raise BudgetExerciseNotFoundError("Não há exercício ativo.")
        guidance = self._repo.get_current_published_guidance(exercise["id"])
        docs = self._repo.list_documents(
            exercise_id=exercise["id"],
            guidance_version_id=guidance["id"] if guidance else None,
            active_only=True,
        )
        return [_public_document(d) for d in docs]

    def list_admin_documents(self, guidance_id: str) -> list[dict[str, Any]]:
        guidance = self._repo.get_guidance(guidance_id)
        if not guidance:
            raise BudgetGuidanceNotFoundError("Orientações não encontradas.")
        docs = self._repo.list_documents(
            exercise_id=guidance["exercise_id"],
            guidance_version_id=guidance_id,
            active_only=False,
        )
        return [_public_document(d) for d in docs]

    def upload_document(
        self,
        actor: BudgetActor,
        *,
        exercise_id: str,
        guidance_id: str | None,
        display_name: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
        description: str | None,
        display_order: int,
        external_url: str | None = None,
        document_kind: str | None = None,
    ) -> dict[str, Any]:
        self.get_exercise(exercise_id)
        if external_url:
            payload = {
                "exercise_id": exercise_id,
                "guidance_version_id": guidance_id,
                "display_name": display_name.strip() or original_name,
                "original_name": original_name or display_name,
                "mime_type": "text/uri-list",
                "size_bytes": 0,
                "document_kind": "external_link",
                "description": description,
                "display_order": display_order,
                "storage_key": None,
                "external_url": external_url.strip(),
                "uploaded_by_user_id": actor.user_id,
                "uploaded_by_name": actor.user_name,
            }
        else:
            storage_key, kind = self._storage.save(
                exercise_id=exercise_id,
                original_name=original_name,
                content=content,
                mime_type=mime_type,
            )
            payload = {
                "exercise_id": exercise_id,
                "guidance_version_id": guidance_id,
                "display_name": display_name.strip() or original_name,
                "original_name": original_name,
                "mime_type": (mime_type or "").lower(),
                "size_bytes": len(content),
                "document_kind": document_kind or kind,
                "description": description,
                "display_order": display_order,
                "storage_key": storage_key,
                "external_url": None,
                "uploaded_by_user_id": actor.user_id,
                "uploaded_by_name": actor.user_name,
            }
        created = self._repo.create_document(payload)
        self._repo.append_audit(
            exercise_id=exercise_id,
            entity_type="support_document",
            entity_id=created["id"],
            action="document.uploaded",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=None,
            after_state=_public_document(created),
        )
        return _public_document(created)

    def update_document(self, actor: BudgetActor, document_id: str, body: dict[str, Any]) -> dict[str, Any]:
        doc = self._repo.get_document(document_id)
        if not doc or doc.get("status") == "archived":
            raise BudgetDocumentNotFoundError("Documento não encontrado.")
        updated = self._repo.update_document(document_id, body)
        self._repo.append_audit(
            exercise_id=doc["exercise_id"],
            entity_type="support_document",
            entity_id=document_id,
            action="document.updated",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=_public_document(doc),
            after_state=updated,
        )
        return updated

    def archive_document(self, actor: BudgetActor, document_id: str) -> dict[str, Any]:
        doc = self._repo.get_document(document_id)
        if not doc:
            raise BudgetDocumentNotFoundError("Documento não encontrado.")
        archived = self._repo.archive_document(document_id, actor_id=actor.user_id)
        self._repo.append_audit(
            exercise_id=doc["exercise_id"],
            entity_type="support_document",
            entity_id=document_id,
            action="document.archived",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=_public_document(doc),
            after_state=archived,
        )
        return archived

    def resolve_download(self, actor: BudgetActor, document_id: str):
        doc = self._repo.get_document(document_id)
        if not doc or doc.get("status") != "active":
            raise BudgetDocumentNotFoundError("Documento não encontrado.")
        if doc.get("document_kind") == "external_link":
            return {"kind": "external", "url": doc.get("external_url"), "document": _public_document(doc)}
        # access: any authenticated with access OR admin; documents are exercise-scoped not private per user
        if "planejamento-orcamentario.access" not in actor.permissions and "planejamento-orcamentario.admin" not in actor.permissions and "planejamento-orcamentario.guidance.view" not in actor.permissions and "planejamento-orcamentario.guidance.manage" not in actor.permissions:
            raise BudgetUserNotAuthorizedError("Sem permissão para baixar documento.")
        path = self._storage.resolve_file(
            exercise_id=doc["exercise_id"],
            storage_key=doc["storage_key"],
        )
        return {
            "kind": "file",
            "path": path,
            "filename": doc.get("original_name") or doc.get("display_name"),
            "mime_type": doc.get("mime_type") or "application/octet-stream",
            "document": _public_document(doc),
        }

    # ---- scopes ----
    def list_scopes(self) -> list[dict[str, Any]]:
        return self._repo.list_scopes(active_only=False)

    def list_org_catalog(self, *, branch: str | None = None) -> dict[str, Any]:
        branch_norm = None
        if branch:
            try:
                branch_norm = normalize_budget_branch(branch)
            except ValueError as exc:
                raise BudgetCostCenterInvalidError(str(exc)) from exc
        cost_centers = [
            serialize_org_cost_center(cc)
            for cc in self._repo.list_org_cost_centers(branch=branch_norm)
        ]
        return {
            "units": self._repo.list_org_units(),
            "areas": self._repo.list_org_areas(),
            "cost_centers": cost_centers,
        }

    def list_erp_cost_centers(self, *, branch: str) -> list[dict[str, Any]]:
        try:
            branch_norm = normalize_budget_branch(branch)
        except ValueError as exc:
            raise BudgetCostCenterInvalidError(str(exc)) from exc
        items = self._erp.list_centros_custo_by_branch(branch=branch_norm)
        # Garante contrato branch/code/description e isolamento por filial
        return [
            {
                "branch": branch_norm,
                "code": str(item.get("code") or "").strip(),
                "description": str(item.get("description") or "").strip(),
            }
            for item in items
            if str(item.get("code") or "").strip()
            and str(item.get("branch") or branch_norm).strip() == branch_norm
        ]

    def create_org_cost_center(self, actor: BudgetActor, body: dict[str, Any]) -> dict[str, Any]:
        code = str(body["code"]).strip()
        name = str(body["name"]).strip()
        unit_code = str(body["unit_code"]).strip()
        try:
            branch = normalize_budget_branch(body.get("branch") or unit_code)
        except ValueError as exc:
            raise BudgetCostCenterInvalidError(str(exc)) from exc
        if unit_code != branch:
            raise BudgetCostCenterInvalidError(
                "Unidade do centro de custo deve coincidir com a filial (01 ou 02)."
            )
        if not name:
            raise BudgetCostCenterInvalidError("Descrição do centro de custo é obrigatória.")
        self._repo.upsert_org_unit(
            branch, body.get("unit_name") or BUDGET_BRANCH_UNIT_NAMES.get(branch, branch)
        )
        area_code = body.get("area_code")
        if area_code:
            self._repo.upsert_org_area(str(area_code), body.get("area_name") or str(area_code), branch)
        created = self._repo.upsert_org_cost_center(
            {
                "branch": branch,
                "code": code,
                "name": name,
                "unit_code": branch,
                "area_code": area_code,
                "source": COST_CENTER_SOURCE_MANUAL,
                "created_by_user_id": actor.user_id,
            }
        )
        public = serialize_org_cost_center(created)
        self._repo.append_audit(
            exercise_id=None,
            entity_type="org_cost_center",
            entity_id=str(created.get("id") or ""),
            action="org_cost_center.upserted",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=None,
            after_state=public,
        )
        return public

    def create_org_cost_center_from_erp(
        self, actor: BudgetActor, body: dict[str, Any]
    ) -> dict[str, Any]:
        """Cadastra CC interno a partir de seleção ERP (sem descrição livre)."""
        try:
            branch = normalize_budget_branch(body.get("branch"))
        except ValueError as exc:
            raise BudgetCostCenterInvalidError(str(exc)) from exc
        code = str(body.get("code") or "").strip()
        unit_id = str(body.get("unit_id") or "").strip()
        if not code:
            raise BudgetCostCenterInvalidError("Código do centro de custo é obrigatório.")
        if not unit_id:
            raise BudgetCostCenterInvalidError("Unidade (filial) é obrigatória.")
        if unit_id != branch:
            raise BudgetCostCenterInvalidError(
                "Unidade incompatível com a filial do centro de custo."
            )
        if body.get("name") or body.get("description"):
            raise BudgetCostCenterInvalidError(
                "Descrição livre não é aceita quando o centro vem do ERP."
            )

        erp_items = self.list_erp_cost_centers(branch=branch)
        erp_match = next((i for i in erp_items if i["code"] == code), None)
        if not erp_match:
            raise BudgetCostCenterNotFoundError(
                "Centro de custo não encontrado na fonte ERP para a filial informada."
            )
        description = str(erp_match.get("description") or "").strip()
        if not description:
            raise BudgetCostCenterInvalidError(
                "Centro de custo ERP sem descrição utilizável."
            )

        existing = self._repo.get_org_cost_center(code, branch=branch)
        if existing and existing.get("active", True):
            raise BudgetCostCenterConflictError(
                "Já existe centro de custo ativo com este código nesta filial."
            )

        self._repo.upsert_org_unit(
            branch, BUDGET_BRANCH_UNIT_NAMES.get(branch, branch)
        )
        created = self._repo.upsert_org_cost_center(
            {
                "branch": branch,
                "code": code,
                "name": description,
                "unit_code": branch,
                "area_code": body.get("area_code"),
                "source": COST_CENTER_SOURCE_ERP,
                "created_by_user_id": actor.user_id,
            }
        )
        public = serialize_org_cost_center(created)
        self._repo.append_audit(
            exercise_id=None,
            entity_type="org_cost_center",
            entity_id=str(created.get("id") or ""),
            action="org_cost_center.from_erp",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=serialize_org_cost_center(existing) if existing else None,
            after_state=public,
        )
        return public

    def create_scope(self, actor: BudgetActor, body: dict[str, Any]) -> dict[str, Any]:
        unit_code = str(body["unit_code"]).strip()
        try:
            unit_code = normalize_budget_branch(unit_code)
        except ValueError as exc:
            raise BudgetScopeConflictError(str(exc)) from exc
        units = {u["code"] for u in self._repo.list_org_units()}
        if unit_code not in units:
            raise BudgetScopeConflictError("Unidade não encontrada no catálogo interno.")
        scope_level = str(body["scope_level"])
        area_code = body.get("area_code")
        cost_center_code = body.get("cost_center_code")
        if scope_level == "cost_center":
            if not cost_center_code:
                raise BudgetScopeConflictError(
                    "Centro de custo deve existir no catálogo interno (sem digitação livre)."
                )
            cc = self._repo.get_org_cost_center(
                str(cost_center_code), branch=unit_code
            )
            if not cc or not cc.get("active", True):
                raise BudgetScopeConflictError(
                    "Centro de custo deve existir no catálogo interno (sem digitação livre)."
                )
        if scope_level == "area":
            areas = {a["code"] for a in self._repo.list_org_areas()}
            if not area_code or str(area_code) not in areas:
                raise BudgetScopeConflictError("Área deve existir no catálogo interno.")
        conflict = self._repo.find_conflicting_scope(
            user_sub=str(body["user_sub"]),
            unit_code=unit_code,
            area_code=str(area_code) if area_code else None,
            cost_center_code=str(cost_center_code) if cost_center_code else None,
            scope_level=scope_level,
        )
        if conflict:
            raise BudgetScopeConflictError("Já existe escopo ativo equivalente para o usuário.")
        created = self._repo.create_scope(
            {
                "user_sub": str(body["user_sub"]),
                "user_name": body.get("user_name"),
                "user_email": body.get("user_email"),
                "unit_code": unit_code,
                "area_code": area_code,
                "cost_center_code": cost_center_code,
                "scope_level": scope_level,
                "role_in_scope": body.get("role_in_scope") or "editor",
                "valid_from": _parse_date(body.get("valid_from"), "valid_from"),
                "valid_to": _parse_date(body.get("valid_to"), "valid_to"),
                "assigned_by_user_id": actor.user_id,
                "assigned_by_name": actor.user_name,
            }
        )
        self._repo.append_audit(
            exercise_id=None,
            entity_type="user_org_scope",
            entity_id=created["id"],
            action="scope.created",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=None,
            after_state=created,
        )
        return created

    def update_scope(self, actor: BudgetActor, scope_id: str, body: dict[str, Any]) -> dict[str, Any]:
        current = self._repo.get_scope(scope_id)
        if not current:
            raise BudgetScopeNotFoundError("Escopo não encontrado.")
        fields = {k: body[k] for k in (
            "user_name", "user_email", "unit_code", "area_code", "cost_center_code",
            "scope_level", "role_in_scope", "valid_from", "valid_to",
        ) if k in body}
        if "valid_from" in fields:
            fields["valid_from"] = _parse_date(fields["valid_from"], "valid_from")
        if "valid_to" in fields:
            fields["valid_to"] = _parse_date(fields["valid_to"], "valid_to")
        updated = self._repo.update_scope(scope_id, fields)
        self._repo.append_audit(
            exercise_id=None,
            entity_type="user_org_scope",
            entity_id=scope_id,
            action="scope.updated",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=current,
            after_state=updated,
        )
        return updated

    def deactivate_scope(self, actor: BudgetActor, scope_id: str) -> dict[str, Any]:
        current = self._repo.get_scope(scope_id)
        if not current:
            raise BudgetScopeNotFoundError("Escopo não encontrado.")
        deactivated = self._repo.deactivate_scope(scope_id, actor_id=actor.user_id)
        self._repo.append_audit(
            exercise_id=None,
            entity_type="user_org_scope",
            entity_id=scope_id,
            action="scope.deactivated",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=current,
            after_state=deactivated,
        )
        return deactivated

    def list_guidance_versions(self, exercise_id: str) -> list[dict[str, Any]]:
        self.get_exercise(exercise_id)
        return self._repo.list_published_guidance(exercise_id)
