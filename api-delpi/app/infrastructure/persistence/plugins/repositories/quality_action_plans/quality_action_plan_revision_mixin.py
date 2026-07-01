from __future__ import annotations

import json
from typing import Any

from app.domain.services.quality_action_plans.action_responsibles_service import (
    build_legacy_action_responsible_fields,
    normalize_responsibles_payload,
)
from app.domain.services.quality_action_plans.five_whys_service import five_whys_json
from app.domain.services.quality_action_plans.ishikawa_causes_service import ishikawa_causes_json
from app.domain.services.quality_action_plans.pac_plan_revision_lock_service import (
    assert_expected_revision_number,
)
from app.domain.services.quality_action_plans.pac_plan_revision_snapshot_service import (
    REVISION_SCOPE_RESTORE,
    VALID_REVISION_SCOPES,
    build_snapshot_from_detail,
    default_revision_summary,
    plan_fields_for_restore,
    validate_snapshot,
)
from app.domain.services.quality_action_plans.quality_action_plan_serialization import serialize_row
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError


class QualityActionPlanRevisionMixin:
    def _pop_expected_revision(self, fields: dict[str, Any]) -> int | None:
        raw = fields.pop("expected_revision_number", None)
        if raw is None:
            return None
        return int(raw)

    def _assert_expected_plan_revision(
        self,
        plan_id: str,
        expected_revision_number: int | None,
    ) -> None:
        if expected_revision_number is None:
            return
        resolved = self._coerce_plan_id(plan_id)
        if not resolved:
            raise PluginsRepositoryError("Plano não encontrado.")
        row = self.fetch_one(
            """
            SELECT current_revision_number
              FROM quality.quality_action_plans
             WHERE id = %s AND deleted_at IS NULL
            """,
            (resolved,),
        )
        if not row:
            raise PluginsRepositoryError("Plano não encontrado.")
        assert_expected_revision_number(
            row.get("current_revision_number"),
            expected_revision_number,
        )

    def _guard_write_revision(
        self,
        plan_id: str,
        expected_revision_number: int | None = None,
        *,
        fields: dict[str, Any] | None = None,
    ) -> None:
        expected = expected_revision_number
        if fields is not None and expected is None:
            expected = self._pop_expected_revision(fields)
        self._assert_expected_plan_revision(plan_id, expected)

    def record_plan_revision(
        self,
        plan_id: str,
        *,
        change_scope: str,
        created_by: str,
        change_summary: str | None = None,
        restored_from_revision: int | None = None,
        created_by_name: str | None = None,
        created_by_email: str | None = None,
        auto_commit: bool = False,
    ) -> int:
        resolved = self._coerce_plan_id(plan_id)
        if not resolved:
            raise PluginsRepositoryError("Plano não encontrado para revisão.")

        scope = (change_scope or "").strip()
        if scope not in VALID_REVISION_SCOPES:
            raise PluginsRepositoryError(f"Escopo de revisão inválido: {scope}")

        detail = self.get_plan_detail(resolved, include_history=False)
        if not detail:
            raise PluginsRepositoryError("Plano não encontrado para snapshot de revisão.")

        snapshot = build_snapshot_from_detail(detail)
        summary = (change_summary or "").strip() or default_revision_summary(scope)

        row = self.fetch_one(
            """
            SELECT COALESCE(MAX(revision_number), 0) + 1 AS next_revision
              FROM quality.quality_action_plan_revisions
             WHERE plan_id = %s
            """,
            (resolved,),
        )
        next_revision = int((row or {}).get("next_revision") or 1)

        self.execute(
            """
            INSERT INTO quality.quality_action_plan_revisions (
                plan_id,
                revision_number,
                snapshot_schema_version,
                snapshot,
                change_scope,
                change_summary,
                restored_from_revision,
                created_by,
                created_by_name,
                created_by_email
            ) VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s)
            """,
            (
                resolved,
                next_revision,
                snapshot["schema_version"],
                json.dumps(snapshot),
                scope,
                summary[:500],
                restored_from_revision,
                created_by,
                created_by_name,
                created_by_email,
            ),
            auto_commit=auto_commit,
        )
        self.execute(
            """
            UPDATE quality.quality_action_plans
               SET current_revision_number = %s,
                   updated_at = NOW()
             WHERE id = %s AND deleted_at IS NULL
            """,
            (next_revision, resolved),
            auto_commit=auto_commit,
        )
        return next_revision

    def list_plan_revisions(
        self,
        plan_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        resolved = self._coerce_plan_id(plan_id)
        if not resolved:
            return {
                "items": [],
                "pagination": {"page": page, "page_size": page_size, "total": 0, "total_pages": 1},
            }

        count_row = self.fetch_one(
            """
            SELECT COUNT(*) AS total
              FROM quality.quality_action_plan_revisions
             WHERE plan_id = %s
            """,
            (resolved,),
        )
        total = int((count_row or {}).get("total") or 0)
        offset = max(page - 1, 0) * page_size
        rows = self.fetch_all(
            """
            SELECT id,
                   plan_id,
                   revision_number,
                   snapshot_schema_version,
                   change_scope,
                   change_summary,
                   restored_from_revision,
                   created_by,
                   created_by_name,
                   created_by_email,
                   created_at
              FROM quality.quality_action_plan_revisions
             WHERE plan_id = %s
             ORDER BY revision_number DESC
             LIMIT %s OFFSET %s
            """,
            (resolved, page_size, offset),
        )
        return {
            "items": [
                serialize_row(row, id_keys=("id", "plan_id")) or {}
                for row in rows
                if row
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": max((total + page_size - 1) // page_size, 1),
            },
        }

    def get_plan_revision(self, plan_id: str, revision_number: int) -> dict[str, Any] | None:
        resolved = self._coerce_plan_id(plan_id)
        if not resolved:
            return None
        row = self.fetch_one(
            """
            SELECT id,
                   plan_id,
                   revision_number,
                   snapshot_schema_version,
                   snapshot,
                   change_scope,
                   change_summary,
                   restored_from_revision,
                   created_by,
                   created_by_name,
                   created_by_email,
                   created_at
              FROM quality.quality_action_plan_revisions
             WHERE plan_id = %s AND revision_number = %s
            """,
            (resolved, revision_number),
        )
        if not row:
            return None
        item = serialize_row(row, id_keys=("id", "plan_id")) or {}
        snapshot = row.get("snapshot")
        if isinstance(snapshot, str):
            item["snapshot"] = json.loads(snapshot)
        else:
            item["snapshot"] = snapshot
        return item

    def apply_plan_snapshot(
        self,
        plan_id: str,
        snapshot: dict[str, Any],
        *,
        auto_commit: bool = False,
    ) -> None:
        resolved = self._coerce_plan_id(plan_id)
        if not resolved:
            raise PluginsRepositoryError("Plano não encontrado para restauração.")

        validate_snapshot(snapshot)
        fields = plan_fields_for_restore(snapshot)
        if fields:
            set_parts = [f"{column} = %s" for column in fields]
            params = list(fields.values()) + [resolved]
            self.execute(
                f"""
                UPDATE quality.quality_action_plans
                   SET {", ".join(set_parts)}, updated_at = NOW()
                 WHERE id = %s AND deleted_at IS NULL
                """,
                tuple(params),
                auto_commit=auto_commit,
            )

        ishikawa = snapshot.get("ishikawa")
        if isinstance(ishikawa, dict):
            causes_json = ishikawa_causes_json(ishikawa)
            self.execute(
                """
                INSERT INTO quality.quality_ishikawa_analysis (
                    plan_id, machine, method_process, material, manpower, measurement, environment, notes
                ) VALUES (%s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s)
                ON CONFLICT (plan_id) DO UPDATE SET
                    machine = EXCLUDED.machine,
                    method_process = EXCLUDED.method_process,
                    material = EXCLUDED.material,
                    manpower = EXCLUDED.manpower,
                    measurement = EXCLUDED.measurement,
                    environment = EXCLUDED.environment,
                    notes = EXCLUDED.notes,
                    updated_at = NOW()
                """,
                (
                    resolved,
                    causes_json["machine"],
                    causes_json["method_process"],
                    causes_json["material"],
                    causes_json["manpower"],
                    causes_json["measurement"],
                    causes_json["environment"],
                    ishikawa.get("notes"),
                ),
                auto_commit=auto_commit,
            )

        five_whys = snapshot.get("five_whys")
        if isinstance(five_whys, dict):
            whys_json = five_whys_json(five_whys)
            self.execute(
                """
                INSERT INTO quality.quality_five_whys (
                    plan_id, occurrence_whys, detection_whys, root_cause, confidence_level
                ) VALUES (%s, %s::jsonb, %s::jsonb, %s, %s)
                ON CONFLICT (plan_id) DO UPDATE SET
                    occurrence_whys = EXCLUDED.occurrence_whys,
                    detection_whys = EXCLUDED.detection_whys,
                    root_cause = EXCLUDED.root_cause,
                    confidence_level = EXCLUDED.confidence_level,
                    updated_at = NOW()
                """,
                (
                    resolved,
                    whys_json["occurrence_whys"],
                    whys_json["detection_whys"],
                    five_whys.get("root_cause"),
                    five_whys.get("confidence_level"),
                ),
                auto_commit=auto_commit,
            )

        team_members = snapshot.get("team_members") or []
        self.execute(
            "DELETE FROM quality.quality_analysis_team_members WHERE plan_id = %s",
            (resolved,),
            auto_commit=auto_commit,
        )
        for index, member in enumerate(team_members):
            if not isinstance(member, dict):
                continue
            name = (member.get("member_name") or "").strip()
            if not name:
                continue
            self.execute(
                """
                INSERT INTO quality.quality_analysis_team_members (
                    plan_id, member_name, member_user_id, department, is_leader, sort_order
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    resolved,
                    name,
                    member.get("member_user_id"),
                    member.get("department"),
                    bool(member.get("is_leader")),
                    member.get("sort_order", index),
                ),
                auto_commit=auto_commit,
            )

        actions = snapshot.get("actions") or []
        snapshot_ids = [str(item["id"]) for item in actions if isinstance(item, dict) and item.get("id")]
        if snapshot_ids:
            self.execute(
                """
                DELETE FROM quality.quality_actions
                 WHERE plan_id = %s
                   AND id <> ALL(%s::uuid[])
                """,
                (resolved, snapshot_ids),
                auto_commit=auto_commit,
            )
        else:
            self.execute(
                "DELETE FROM quality.quality_actions WHERE plan_id = %s",
                (resolved,),
                auto_commit=auto_commit,
            )

        for action in actions:
            if not isinstance(action, dict) or not action.get("id"):
                continue
            responsibles = normalize_responsibles_payload(
                action.get("responsibles"),
                legacy_user_id=action.get("responsible_user_id"),
                legacy_name=action.get("responsible_name"),
            )
            legacy_user_id, legacy_name = build_legacy_action_responsible_fields(responsibles)
            action_id = str(action["id"])
            self.execute(
                """
                INSERT INTO quality.quality_actions (
                    id, plan_id, action_type, description, responsible_user_id,
                    responsible_name, department, due_date, status, evidence_required, cause_track
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    action_type = EXCLUDED.action_type,
                    description = EXCLUDED.description,
                    responsible_user_id = EXCLUDED.responsible_user_id,
                    responsible_name = EXCLUDED.responsible_name,
                    department = EXCLUDED.department,
                    due_date = EXCLUDED.due_date,
                    status = EXCLUDED.status,
                    evidence_required = EXCLUDED.evidence_required,
                    cause_track = EXCLUDED.cause_track,
                    updated_at = NOW()
                """,
                (
                    action_id,
                    resolved,
                    action["action_type"],
                    action["description"],
                    legacy_user_id,
                    legacy_name,
                    action.get("department"),
                    action.get("due_date"),
                    action.get("status", "pending"),
                    action.get("evidence_required", False),
                    action.get("cause_track"),
                ),
                auto_commit=auto_commit,
            )
            self._replace_action_responsibles(action_id, responsibles, auto_commit=auto_commit)

        for evidence in snapshot.get("evidences") or []:
            if not isinstance(evidence, dict) or not evidence.get("id"):
                continue
            self.execute(
                """
                UPDATE quality.quality_problem_evidences
                   SET type = COALESCE(%s, type),
                       section = COALESCE(%s, section),
                       description = %s,
                       knowledge_visible = COALESCE(%s, knowledge_visible),
                       action_id = %s
                 WHERE id = %s AND plan_id = %s
                """,
                (
                    evidence.get("type"),
                    evidence.get("section"),
                    evidence.get("description"),
                    evidence.get("knowledge_visible"),
                    evidence.get("action_id"),
                    evidence["id"],
                    resolved,
                ),
                auto_commit=auto_commit,
            )

    def restore_plan_revision(
        self,
        plan_id: str,
        revision_number: int,
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
    ) -> dict[str, Any] | None:
        resolved = self._coerce_plan_id(plan_id)
        if not resolved:
            return None
        if not self.get_plan_by_id(resolved):
            return None

        revision = self.get_plan_revision(resolved, revision_number)
        if not revision:
            raise ValueError("Revisão não encontrada.")

        snapshot = revision.get("snapshot")
        if not isinstance(snapshot, dict):
            raise ValueError("Snapshot da revisão inválido.")

        self.apply_plan_snapshot(resolved, snapshot, auto_commit=False)
        new_revision = self.record_plan_revision(
            resolved,
            change_scope=REVISION_SCOPE_RESTORE,
            change_summary=f"Restaurado da revisão {revision_number}.",
            restored_from_revision=revision_number,
            created_by=updated_by,
            created_by_name=updated_by_name,
            created_by_email=updated_by_email,
            auto_commit=False,
        )
        self.append_history(
            plan_id=resolved,
            event_type="plan_revision_restored",
            created_by=updated_by,
            created_by_name=updated_by_name,
            created_by_email=updated_by_email,
            old_value=str(revision_number),
            new_value=str(new_revision),
            comment=f"Plano restaurado para a revisão {revision_number}.",
            auto_commit=False,
        )
        self.commit()
        return self.get_plan_detail(resolved)
