"""GLPI #887: guarded selective activation of TEN verified manager schedules.

Default mode is a read-only preview. No message is sent by this script.
Activation requires the api-delpi GLOBAL gate already active, a deliberate
confirmation argument and a current successful Core↔RH identity check.
Do not enable the GLOBAL gate for any other purpose without review.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import sys
from typing import Any
from uuid import UUID

from app.application.use_cases.reports.report_recipients_schedule_use_cases import (
    UpsertReportScheduleUseCase,
)
from app.composition.reports_composer import build_reports_repository
from app.config import settings
from app.domain.services.reports.direct_weekly_team_delivery_policy import (
    ensure_manager_is_sole_recipient,
)
from app.domain.services.reports.providers.team_direct_app_opens_weekly_provider import (
    DirectTeamUsageWeeklyProvider,
)
from app.scripts.glpi_887_prepare_manager_reports import (
    PROVIDER,
    fetch_candidates,
)

ROOT = "10257"
EXCLUDED = frozenset({"20057", "20077"})
APPROVED = frozenset({
    "10008", "10257", "10420", "10500", "10728",
    "20001", "20002", "20200", "20410", "PJ - 004",
})
EXPECTED = APPROVED | EXCLUDED
CONFIRM_PHRASE = "ATIVAR_10"
TIMEZONE = "America/Sao_Paulo"


def _schedule_matches(schedule: dict[str, Any] | None) -> bool:
    return (
        isinstance(schedule, dict)
        and schedule.get("scheduleKind") == "weekly"
        and schedule.get("weekday") == 0
        and schedule.get("hour") == 8
        and schedule.get("minute") == 0
        and schedule.get("timezone") == TIMEZONE
    )


def _future_schedule(schedule: dict[str, Any]) -> bool:
    value = schedule.get("nextRunAt")
    if not isinstance(value, str) or not value:
        return False
    try:
        next_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    if next_at.tzinfo is None:
        return False
    return next_at > datetime.now(timezone.utc)


def build_plan(
    *,
    candidates: list[dict[str, Any]],
    definitions: list[dict[str, Any]],
    repository: Any,
    provider: Any,
) -> list[dict[str, Any]]:
    by_reg = {person.get("registration"): person for person in candidates}
    if len(by_reg) != len(candidates) or set(by_reg) != EXPECTED:
        raise ValueError(
            "A hierarquia RH mudou ou está incompleta. "
            "Exigir novamente os 12 gestores conhecidos antes de ativar."
        )
    if any(person.get("status") != "ready" for person in candidates):
        raise ValueError("Há gestor sem conta Core verificada: interromper.")

    all_weekly = [d for d in definitions if d.get("providerKey") == PROVIDER]
    definition_counts = Counter(
        (d.get("params") or {}).get("managerRegistration") for d in all_weekly
    )
    if any(definition_counts[reg] != 1 for reg in EXPECTED):
        raise ValueError("Definição ausente ou duplicada para gestor RH.")

    # Never switch the global gate on in the presence of an unexpected
    # already-enabled direct-team schedule outside the approved root.
    for definition in all_weekly:
        reg = (definition.get("params") or {}).get("managerRegistration")
        if reg not in EXPECTED:
            schedule = repository.get_schedule_for_definition(definition["id"])
            if schedule and schedule.get("enabled"):
                raise ValueError(
                    "Agenda de equipe direta fora da lista autorizada está ativa."
                )

    plan = []
    for reg in sorted(EXPECTED):
        person = by_reg[reg]
        definition = next(
            d for d in all_weekly
            if (d.get("params") or {}).get("managerRegistration") == reg
        )
        params = definition.get("params") or {}
        if not definition.get("active") or "weekStart" in params:
            raise ValueError("Definição inativa ou período fixado para " + reg)
        if params != {"managerRegistration": reg}:
            raise ValueError("Parâmetros extras na definição RH " + reg)

        schedule = repository.get_schedule_for_definition(definition["id"])
        if not _schedule_matches(schedule):
            raise ValueError("Agenda semanal divergente para " + reg)
        if reg in EXCLUDED and schedule["enabled"]:
            raise ValueError("Gestora excluída apresenta agenda ativa: " + reg)
        if schedule["enabled"] and not _future_schedule(schedule):
            raise ValueError("Agenda ativa sem próxima execução futura para " + reg)

        recipients = repository.list_active_recipients(definition["id"])
        all_recipients = repository.list_recipients(definition["id"])
        if len(recipients) != 1 or len(all_recipients) != 1:
            raise ValueError("Destinatário único não confirmado para " + reg)
        try:
            source_user_id = str(UUID(str(person["userId"])))
            recipient_user_id = str(UUID(str(recipients[0]["userId"])))
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError("Identidade Core inválida para " + reg) from exc
        if (
            source_user_id != recipient_user_id
            or not isinstance(person.get("email"), str)
            or str(recipients[0].get("email") or "").strip().casefold()
               != person["email"].strip().casefold()
        ):
            raise ValueError("Destinatário não coincide com RH/Core para " + reg)

        # Independent authorization proof from the same provider used
        # during real scheduled deliveries, with explicit direct-only scope.
        dataset = provider.collect({"managerRegistration": reg})
        ensure_manager_is_sole_recipient(recipients=recipients, dataset=dataset)
        if dataset.row_count != person.get("directCount"):
            raise ValueError("Quantidade de diretos alterada para " + reg)

        plan.append({
            "registration": reg,
            "definitionId": definition["id"],
            "enabled": bool(schedule["enabled"]),
            "desiredEnabled": reg in APPROVED,
            "nextRunAt": schedule.get("nextRunAt"),
        })
    return plan


def apply_plan(plan: list[dict[str, Any]], repository: Any) -> None:
    if not settings.REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED:
        raise ValueError(
            "Gate global está OFF. Configure-o no container api-delpi "
            "antes de ativar as agendas."
        )
    manager_schedules = UpsertReportScheduleUseCase(repository)
    for row in plan:
        if not row["desiredEnabled"]:
            # Never touch either excluded manager; fail closed above.
            continue
        if row["enabled"]:
            continue
        manager_schedules.execute(
            definition_id=row["definitionId"],
            schedule_kind="weekly",
            weekday=0,
            hour=8,
            minute=0,
            enabled=True,
            timezone_name=TIMEZONE,
        )


def _summary(plan: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "scope": "official_rh_root_10257",
        "expectedManagers": len(EXPECTED),
        "approved": len(APPROVED),
        "excludedRegistrations": sorted(EXCLUDED),
        "currentlyEnabled": sum(x["enabled"] for x in plan),
        "stillToEnable": sum(
            x["desiredEnabled"] and not x["enabled"] for x in plan
        ),
        "excludedDisabled": all(
            not x["enabled"] for x in plan if not x["desiredEnabled"]
        ),
        "nextScheduledForApproved": {
            x["registration"]: x["nextRunAt"]
            for x in plan if x["desiredEnabled"] and x["enabled"]
        },
        "noEmailSentByThisCommand": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="GLPI 887: prévia e ativação seletiva EXATA dos 10 gestores"
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)
    if args.apply and args.confirm != CONFIRM_PHRASE:
        parser.error("--apply exige --confirm ATIVAR_10")
    if args.confirm and not args.apply:
        parser.error("--confirm somente com --apply")

    try:
        candidates = fetch_candidates(
            [ROOT],
            core_base_url=settings.CORE_API_BASE_URL or "",
            token=settings.CORE_REPORTS_DIRECT_USAGE_SERVICE_TOKEN or "",
        )
        repo = build_reports_repository()
        provider = DirectTeamUsageWeeklyProvider(
            core_base_url=settings.CORE_API_BASE_URL,
            service_token=settings.CORE_REPORTS_DIRECT_USAGE_SERVICE_TOKEN,
        )
        plan = build_plan(
            candidates=candidates,
            definitions=repo.list_definitions(),
            repository=repo,
            provider=provider,
        )
        if args.apply:
            apply_plan(plan, repo)
            plan = build_plan(
                candidates=candidates,
                definitions=repo.list_definitions(),
                repository=repo,
                provider=provider,
            )
            if _summary(plan)["stillToEnable"]:
                raise RuntimeError("Ativação incompleta; consultar estado antes de repetir.")
        result = _summary(plan)
        result["changesApplied"] = bool(args.apply)
        result["deliveryGateEnabled"] = bool(
            settings.REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, RuntimeError) as exc:
        print("BLOQUEADO:", str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
