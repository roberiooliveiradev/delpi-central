from __future__ import annotations

from typing import Any, Literal

from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_admin_config_bundle_repository import (
    PostgresStrategicIndicatorsAdminConfigBundleRepository,
)

AdminConfigImportMode = Literal["merge", "replace"]


def _planned(
    *,
    in_file: int = 0,
    insert: int = 0,
    update: int = 0,
    skip: int = 0,
    delete: int = 0,
) -> dict[str, int]:
    return {
        "in_file": in_file,
        "insert": insert,
        "update": update,
        "skip": skip,
        "delete": delete,
    }


class AdminConfigBundleService:
    def __init__(
        self,
        repository: PostgresStrategicIndicatorsAdminConfigBundleRepository,
    ) -> None:
        self._repository = repository

    def preview(
        self,
        *,
        bundle: dict,
        mode: AdminConfigImportMode = "replace",
        include_goals: bool = True,
    ) -> dict[str, Any]:
        self._require_envelope(bundle)
        errors = self._content_errors(bundle=bundle, mode=mode)
        current = self._repository.count_catalog()
        planned = self._plan(
            bundle=bundle,
            mode=mode,
            include_goals=include_goals,
            current=current,
        )
        return {
            "valid": not errors,
            "errors": errors,
            "mode": mode,
            "current_counts": current,
            "planned": planned,
        }

    def apply(
        self,
        *,
        bundle: dict,
        actor_user_id: str | None,
        mode: AdminConfigImportMode = "replace",
        include_goals: bool = True,
    ) -> dict[str, Any]:
        preview = self.preview(
            bundle=bundle,
            mode=mode,
            include_goals=include_goals,
        )
        if not preview["valid"]:
            errors = preview.get("errors") or ["Pacote inválido."]
            raise ValueError("; ".join(str(item) for item in errors))

        effective_include_goals = True if mode == "replace" else include_goals
        return self._repository.import_bundle(
            bundle=bundle,
            actor_user_id=actor_user_id,
            include_goals=effective_include_goals,
            mode=mode,
        )

    def _require_envelope(self, bundle: dict) -> None:
        if not isinstance(bundle, dict):
            raise ValueError("Pacote de importação inválido.")
        schema_version = int(bundle.get("schema_version") or 0)
        expected = PostgresStrategicIndicatorsAdminConfigBundleRepository.SCHEMA_VERSION
        if schema_version != expected:
            raise ValueError(f"schema_version incompatível: esperado {expected}.")

    def _content_errors(self, *, bundle: dict, mode: AdminConfigImportMode) -> list[str]:
        errors: list[str] = []
        departments = bundle.get("departments") or []
        indicators = bundle.get("department_indicators") or []
        goals = bundle.get("indicator_goals") or []

        file_dept_ids: set[str] = set()
        for row in departments:
            if not isinstance(row, dict):
                errors.append("Departamento inválido no pacote de importação.")
                continue
            department_id = str(row.get("department_id") or "").strip()
            if not department_id:
                errors.append("department_id obrigatório no pacote de importação.")
                continue
            file_dept_ids.add(department_id)

        existing_dept_ids = (
            set() if mode == "replace" else self._repository.list_department_ids()
        )
        known_dept_ids = file_dept_ids | existing_dept_ids

        file_indicator_ids: set[str] = set()
        for row in indicators:
            if not isinstance(row, dict):
                errors.append("Indicador inválido no pacote de importação.")
                continue
            indicator_id = str(row.get("indicator_id") or "").strip()
            department_id = str(row.get("department_id") or "").strip()
            if not indicator_id or not department_id:
                errors.append(
                    "indicator_id e department_id são obrigatórios no pacote de importação."
                )
                continue
            file_indicator_ids.add(indicator_id)
            if department_id not in known_dept_ids:
                errors.append(
                    f"Indicador {indicator_id} sem department_id no arquivo"
                )

        existing_indicator_ids = (
            set() if mode == "replace" else self._repository.list_indicator_ids()
        )
        known_indicator_ids = file_indicator_ids | existing_indicator_ids

        for row in goals:
            if not isinstance(row, dict):
                errors.append("Meta inválida no pacote de importação.")
                continue
            indicator_id = str(row.get("indicator_id") or "").strip()
            try:
                goal_year = int(row.get("goal_year") or 0)
            except (TypeError, ValueError):
                goal_year = 0
            if not indicator_id or goal_year < 2020 or goal_year > 2100:
                errors.append("Meta inválida no pacote de importação.")
                continue
            if indicator_id not in known_indicator_ids:
                errors.append(
                    f"Meta do indicador {indicator_id} sem indicador no arquivo"
                )

        return errors

    def _plan(
        self,
        *,
        bundle: dict,
        mode: AdminConfigImportMode,
        include_goals: bool,
        current: dict[str, int],
    ) -> dict[str, dict[str, int]]:
        departments = [
            row for row in (bundle.get("departments") or []) if isinstance(row, dict)
        ]
        indicators = [
            row
            for row in (bundle.get("department_indicators") or [])
            if isinstance(row, dict)
        ]
        goals = [
            row for row in (bundle.get("indicator_goals") or []) if isinstance(row, dict)
        ]
        module_settings = bundle.get("module_settings") or {}
        settings_in_file = sum(
            1
            for key in ("parameters", "governance")
            if isinstance(module_settings, dict) and module_settings.get(key) is not None
        )

        if mode == "replace":
            effective_goals = [
                row for row in goals if bool(row.get("is_active", True))
            ]
            return {
                "departments": _planned(
                    in_file=len(departments),
                    insert=len(departments),
                    delete=current.get("departments", 0),
                ),
                "department_indicators": _planned(
                    in_file=len(indicators),
                    insert=len(indicators),
                    delete=current.get("department_indicators", 0),
                ),
                "indicator_goals": _planned(
                    in_file=len(goals),
                    insert=len(effective_goals),
                    skip=len(goals) - len(effective_goals),
                    delete=current.get("indicator_goals", 0),
                ),
                "module_settings": _planned(
                    in_file=settings_in_file,
                    update=settings_in_file,
                ),
            }

        existing_depts = self._repository.list_department_ids()
        existing_indicators = self._repository.list_indicator_ids()
        existing_goals = self._repository.list_active_goal_keys()

        dept_insert = dept_update = 0
        for row in departments:
            department_id = str(row.get("department_id") or "").strip()
            if not department_id:
                continue
            if department_id in existing_depts:
                dept_update += 1
            else:
                dept_insert += 1

        ind_insert = ind_update = 0
        for row in indicators:
            indicator_id = str(row.get("indicator_id") or "").strip()
            if not indicator_id:
                continue
            if indicator_id in existing_indicators:
                ind_update += 1
            else:
                ind_insert += 1

        goal_insert = goal_skip = 0
        for row in goals:
            if not include_goals or not bool(row.get("is_active", True)):
                goal_skip += 1
                continue
            indicator_id = str(row.get("indicator_id") or "").strip()
            try:
                goal_year = int(row.get("goal_year") or 0)
            except (TypeError, ValueError):
                goal_skip += 1
                continue
            branch = str(row.get("goal_scope_branch") or "").strip()
            if (indicator_id, goal_year, branch) in existing_goals:
                goal_skip += 1
            else:
                goal_insert += 1

        return {
            "departments": _planned(
                in_file=len(departments),
                insert=dept_insert,
                update=dept_update,
            ),
            "department_indicators": _planned(
                in_file=len(indicators),
                insert=ind_insert,
                update=ind_update,
            ),
            "indicator_goals": _planned(
                in_file=len(goals),
                insert=goal_insert,
                skip=goal_skip,
            ),
            "module_settings": _planned(
                in_file=settings_in_file,
                update=settings_in_file,
            ),
        }
