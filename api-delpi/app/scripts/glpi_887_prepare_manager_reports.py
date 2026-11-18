"""GLPI #887: prepare one DISABLED weekly report per verified direct manager.

Usage inside api-delpi container:
  python -m app.scripts.glpi_887_prepare_manager_reports --root 20001
  python -m app.scripts.glpi_887_prepare_manager_reports --root 20001 --apply --confirm PREPARAR

Supply every independent official RH root separately. The default is
read-only. No send, no Graph, no user-identity changes, no schedule enabled.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from urllib.parse import quote
from uuid import UUID

import requests

from app.application.use_cases.reports.report_recipients_schedule_use_cases import (
    ReplaceReportRecipientsUseCase,
    UpsertReportScheduleUseCase,
)
from app.composition.reports_composer import build_reports_repository
from app.config import settings

PROVIDER = "team_direct_app_opens_weekly"
PREFIX = "Acessos semanais | Gestor RH "
MAX_ROOTS = 12
MAX_CANDIDATES = 250


def _validate_registration(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Matrícula de origem inválida.")
    reg = value.strip()
    if not reg or len(reg) > 30 or any(c in reg for c in "/?#\\\r\n\x00"):
        raise ValueError("Matrícula de origem inválida.")
    return reg


def fetch_candidates(
    roots: list[str],
    *,
    core_base_url: str,
    token: str,
    session=requests,
) -> list[dict]:
    if not roots or len(roots) > MAX_ROOTS:
        raise ValueError(f"Informe de 1 a {MAX_ROOTS} raízes RH.")
    normalized = [_validate_registration(root) for root in roots]
    if len(set(normalized)) != len(normalized):
        raise ValueError("Raízes RH duplicadas.")
    base = (core_base_url or "").rstrip("/")
    if not base.startswith(("https://", "http://")) or not token:
        raise ValueError("Credencial/URL S2S dos relatórios não configuradas.")

    found: dict[str, dict] = {}
    for root in normalized:
        url = (
            base
            + "/integrations/organization/managers/"
            + quote(root, safe="")
            + "/reports/eligible-managers"
        )
        try:
            response = session.get(
                url,
                headers={"X-Delpi-Service-Token": token},
                timeout=30,
                allow_redirects=False,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise ValueError(
                f"Falha ao consultar hierarquia RH da raiz {root}. Nenhuma alteração realizada."
            ) from exc
        if (
            not isinstance(data, dict)
            or data.get("rootRegistration") != root
            or data.get("scopedToRoot") is not True
            or data.get("readOnly") is not True
            or not isinstance(data.get("candidates"), list)
            or data.get("managerCount") != len(data["candidates"])
        ):
            raise ValueError(f"Contrato inválido para raiz {root}. Nenhuma alteração realizada.")

        for item in data["candidates"]:
            if not isinstance(item, dict):
                raise ValueError("Candidato RH inválido.")
            reg = _validate_registration(item.get("registration"))
            status = item.get("status")
            direct_count = item.get("directCount")
            if (
                status not in {"ready", "missing_mapping", "missing_email"}
                or type(direct_count) is not int
                or direct_count <= 0
                or not isinstance(item.get("fullName"), str)
            ):
                raise ValueError("Dados inválidos de gestor RH.")
            if status == "ready":
                try:
                    UUID(str(item.get("userId")))
                except (TypeError, ValueError) as exc:
                    raise ValueError("UUID de gestor inválido.") from exc
                email = item.get("email")
                if not isinstance(email, str) or "@" not in email or "***" in email:
                    raise ValueError("E-mail de gestor inválido.")
            elif item.get("userId") is not None or item.get("email") is not None:
                raise ValueError("Dados pessoais de gestor inelegível não devem ser enviados.")
            previous = found.get(reg)
            if previous is not None:
                for field in ("status", "directCount", "userId", "email"):
                    if previous.get(field) != item.get(field):
                        raise ValueError(
                            f"Dados divergentes entre hierarquias para matrícula {reg}."
                        )
            else:
                found[reg] = item
            if len(found) > MAX_CANDIDATES:
                raise ValueError("Máximo de 250 gestores por preparação.")

    return [found[key] for key in sorted(found)]


def make_plan(candidates: list[dict], definitions: list[dict]) -> list[dict]:
    by_registration: dict[str, list[dict]] = {}
    for definition in definitions:
        if definition.get("providerKey") != PROVIDER:
            continue
        params = definition.get("params") or {}
        if not isinstance(params, dict):
            raise ValueError("Definição de Reports com parâmetros inválidos.")
        reg = _validate_registration(params.get("managerRegistration"))
        by_registration.setdefault(reg, []).append(definition)

    plan = []
    for item in candidates:
        reg = item["registration"]
        current = by_registration.get(reg, [])
        if len(current) > 1:
            operation = "duplicate_definitions"
        elif current:
            operation = "already_exists"
        elif item["status"] == "ready":
            operation = "prepare_disabled"
        else:
            operation = item["status"]
        plan.append({
            "registration": reg,
            "directCount": item["directCount"],
            "operation": operation,
            "recipient": (
                {"userId": item["userId"], "email": item["email"]}
                if operation == "prepare_disabled" else None
            ),
        })
    return plan


def apply_plan(plan: list[dict], repository) -> dict:
    recipients = ReplaceReportRecipientsUseCase(repository)
    schedules = UpsertReportScheduleUseCase(repository)
    created = []
    try:
        for item in plan:
            if item["operation"] != "prepare_disabled":
                continue
            reg = item["registration"]
            row = repository.create_definition(
                name=PREFIX + reg,
                provider_key=PROVIDER,
                params={"managerRegistration": reg},
                active=True,
                created_by_user_id=None,
            )
            definition_id = str(row["id"])
            # Fixed single recipient and a DISABLED Monday 08:00 schedule.
            recipients.execute(
                definition_id=definition_id,
                items=[item["recipient"]],
            )
            schedules.execute(
                definition_id=definition_id,
                schedule_kind="weekly",
                weekday=0,
                hour=8,
                minute=0,
                enabled=False,
                timezone_name="America/Sao_Paulo",
            )
            created.append(reg)
    except Exception as exc:
        raise RuntimeError(
            "Preparação interrompida. Uma definição pode ter ficado parcial; "
            "verifique no Delpi Reports antes de executar novamente."
        ) from exc
    return {"prepared": len(created), "registrations": created}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="GLPI #887 - prévia e preparo em lote sem envio de e-mails"
    )
    parser.add_argument(
        "--root", action="append", required=True,
        help="Matrícula raiz oficial RH; repetir para cada árvore independente.",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Preparar definições e agendas DESABILITADAS após prévia.",
    )
    parser.add_argument(
        "--confirm", default="",
        help="Escreva PREPARAR somente com --apply.",
    )
    args = parser.parse_args(argv)
    if args.apply and args.confirm != "PREPARAR":
        parser.error("--apply exige --confirm PREPARAR")
    if args.confirm and not args.apply:
        parser.error("--confirm exige --apply")
    if args.apply and settings.REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED:
        parser.error("Envio automático deve permanecer DESATIVADO no preparo.")

    try:
        candidates = fetch_candidates(
            args.root,
            core_base_url=settings.CORE_API_BASE_URL or "",
            token=settings.CORE_REPORTS_DIRECT_USAGE_SERVICE_TOKEN or "",
        )
        repo = build_reports_repository()
        plan = make_plan(candidates, repo.list_definitions())
        counts: dict[str, int] = {}
        for item in plan:
            code = item["operation"]
            counts[code] = counts.get(code, 0) + 1
        summary = {
            "scopedToRoots": args.root,
            "totalManagersFound": len(plan),
            "counts": counts,
            "changesApplied": False,
            "deliveryEnabled": False,
            "caution": "Cobertura limitada às hierarquias raízes informadas.",
        }
        if args.apply:
            if counts.get("duplicate_definitions"):
                raise ValueError("Definições duplicadas: corrija antes de preparar.")
            result = apply_plan(plan, repo)
            summary["changesApplied"] = True
            summary["prepared"] = result["prepared"]
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, RuntimeError) as exc:
        print("ERRO:", str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
