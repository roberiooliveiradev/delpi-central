"""Delpi Reports provider: weekly recorded app opens of DIRECT RH reports only.

The Core API is authoritative for hierarchy, verified manager recipient and
consent. This provider neither expands an org tree nor chooses recipients.
"""

from __future__ import annotations

import html
import logging
from datetime import date, timedelta
from typing import Any, Mapping
from urllib.parse import quote
from uuid import UUID

import requests

from app.domain.services.reports.report_email_brand_layout_service import (
    GRAY_600,
    ReportEmailBrandLayoutService,
)
from app.domain.services.reports.report_types import EmailPayload, ReportDataset

logger = logging.getLogger(__name__)

PROVIDER_KEY = "team_direct_app_opens_weekly"
PROVIDER_NAME = "Acessos semanais - subordinados diretos"
_ALLOWED_STATUSES = frozenset({
    "unmapped", "consent_not_granted", "no_recorded_opens", "recorded_opens",
})


class DirectTeamUsageWeeklyProvider:
    def __init__(
        self,
        *,
        core_base_url: str,
        service_token: str,
        timeout_seconds: float = 15.0,
        session: Any = None,
    ) -> None:
        self.core_base_url = (core_base_url or "").rstrip("/")
        self.service_token = (service_token or "").strip()
        self.timeout_seconds = timeout_seconds
        self.session = session or requests

    @property
    def key(self) -> str:
        return PROVIDER_KEY

    def describe_params(self) -> Mapping[str, Any]:
        return {
            "type": "object",
            "required": ["managerRegistration"],
            "properties": {
                "managerRegistration": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 30,
                    "description": "Matrícula RH textual do gestor, preservando zeros.",
                },
                "weekStart": {
                    "type": "string",
                    "format": "date",
                    "description": "Segunda-feira da semana já concluída; omitir para a anterior.",
                },
            },
            "displayName": PROVIDER_NAME,
        }

    def collect(
        self,
        params: Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
    ) -> ReportDataset:
        del context
        if not isinstance(params, Mapping):
            raise ValueError("Parâmetros do relatório inválidos.")
        if set(params) - {"managerRegistration", "weekStart"}:
            raise ValueError("Parâmetros não permitidos; escopo direto é fixo.")
        reg = params.get("managerRegistration")
        if not isinstance(reg, str):
            raise ValueError("managerRegistration deve ser uma matrícula textual.")
        registration = reg.strip()
        if (
            not registration or len(registration) > 30
            or any(c in registration for c in "/?#\\\r\n\x00")
        ):
            raise ValueError("managerRegistration inválida.")

        week_start = params.get("weekStart")
        if week_start is not None:
            if not isinstance(week_start, str):
                raise ValueError("weekStart deve ser AAAA-MM-DD.")
            try:
                d = date.fromisoformat(week_start)
            except ValueError as exc:
                raise ValueError("weekStart deve ser AAAA-MM-DD.") from exc
            if d.isoformat() != week_start:
                raise ValueError("weekStart deve ser AAAA-MM-DD.")

        if not self.core_base_url.startswith(("http://", "https://")):
            raise ValueError("Core API URL não configurada.")
        if not self.service_token:
            raise ValueError("Credencial exclusiva de Reports não configurada.")

        path = (
            "/integrations/organization/managers/"
            + quote(registration, safe="")
            + "/reports/direct-weekly-opens"
        )
        try:
            response = self.session.get(
                self.core_base_url + path,
                headers={"X-Delpi-Service-Token": self.service_token},
                params={"week_start": week_start} if week_start else None,
                timeout=self.timeout_seconds,
                allow_redirects=False,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("direct_weekly_core_read_failed")
            raise ValueError("Dados de acessos diretos indisponíveis na Core API.") from exc

        if not isinstance(data, dict):
            raise ValueError("Contrato de acessos da Core API inválido.")
        if (
            data.get("source") != "app_usage_events"
            or data.get("managerRegistration") != registration
            or data.get("includeIndirect") is not False
            or data.get("directOnly") is not True
            or not isinstance(data.get("members"), list)
            or data.get("teamCount") != len(data["members"])
        ):
            raise ValueError("Core API não confirmou escopo exclusivo de subordinados diretos.")

        recipient = data.get("recipient")
        if not isinstance(recipient, dict):
            raise ValueError("Destinatário gestor não verificado.")
        manager_id = recipient.get("userId")
        manager_email = recipient.get("email")
        try:
            manager_id = str(UUID(str(manager_id)))
        except (TypeError, ValueError) as exc:
            raise ValueError("Identidade Core do gestor não verificada.") from exc
        if (
            not isinstance(manager_email, str)
            or "@" not in manager_email
            or "***" in manager_email
        ):
            raise ValueError("E-mail do gestor não confirmado.")

        rows = []
        seen = set()
        for item in data["members"]:
            if not isinstance(item, dict):
                raise ValueError("Colaborador inválido na resposta Core.")
            registration_member = item.get("registration")
            if (
                item.get("relationship") != "direct"
                or not isinstance(registration_member, str)
                or not registration_member
                or registration_member == registration
                or registration_member in seen
                or item.get("usageStatus") not in _ALLOWED_STATUSES
            ):
                raise ValueError("A resposta Core incluiu vínculo fora do escopo direto.")
            seen.add(registration_member)
            name = item.get("fullName")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Colaborador RH sem nome.")
            status = item["usageStatus"]
            recorded = item.get("totalRecordedOpens")
            apps = item.get("apps")
            if not isinstance(apps, list):
                raise ValueError("Lista de aplicativos inválida.")
            app_details = []
            if status in {"unmapped", "consent_not_granted"}:
                if recorded is not None or apps:
                    raise ValueError("Dados de uso não autorizados em membro sem cobertura.")
                total = None
                apps_description = "Dados indisponíveis"
            else:
                if isinstance(recorded, bool) or not isinstance(recorded, int) or recorded < 0:
                    raise ValueError("Quantidade registrada inválida.")
                total = recorded
                if status == "no_recorded_opens" and (total != 0 or apps):
                    raise ValueError("Status de uso inconsistente.")
                if status == "recorded_opens" and total <= 0:
                    raise ValueError("Status de uso inconsistente.")
                checked_apps = []
                summed = 0
                for app in apps:
                    if not isinstance(app, dict):
                        raise ValueError("Aplicativo inválido.")
                    app_name = app.get("appName")
                    count = app.get("recordedOpens")
                    if not isinstance(app_name, str) or not app_name.strip():
                        raise ValueError("Nome de aplicativo inválido.")
                    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
                        raise ValueError("Aberturas inválidas.")
                    summed += count
                    checked_apps.append(f"{app_name}: {count}")
                    sessions = app.get("recordedSessions", 0)
                    duration = app.get("totalDurationSeconds", 0)
                    mean = app.get("avgSessionSeconds")
                    if (
                        isinstance(sessions, bool)
                        or not isinstance(sessions, int)
                        or sessions < 0
                        or isinstance(duration, bool)
                        or not isinstance(duration, int)
                        or duration < 0
                    ):
                        raise ValueError("Duração registrada inválida.")
                    if sessions == 0:
                        if duration != 0 or mean is not None:
                            raise ValueError("Média sem sessões registradas.")
                    elif (
                        duration < sessions
                        or isinstance(mean, bool)
                        or not isinstance(mean, int)
                        or mean != round(duration / sessions)
                    ):
                        raise ValueError("Média de sessão inconsistente.")
                    app_details.append({
                        "name": app_name.strip(),
                        "recordedOpens": count,
                        "recordedSessions": sessions,
                        "avgSessionSeconds": mean,
                    })
                if summed != total:
                    raise ValueError("Total de aberturas divergente.")
                apps_description = "; ".join(checked_apps) if total else "Sem abertura registrada"

            rows.append({
                "registration": registration_member,
                "collaborator": name.strip(),
                "recordedOpens": total,
                "applications": apps_description,
                "appDetails": app_details,
            })

        monday = data.get("weekStart")
        end_exclusive = data.get("weekEndExclusive")
        try:
            start = date.fromisoformat(monday)
            until = date.fromisoformat(end_exclusive)
        except (TypeError, ValueError) as exc:
            raise ValueError("Período de uso inválido.") from exc
        if monday != start.isoformat() or until != start + timedelta(days=7):
            raise ValueError("Intervalo semanal da Core API inválido.")
        if data.get("timezone") != "America/Sao_Paulo":
            raise ValueError("Fuso de uso não autorizado.")

        rows.sort(key=lambda row: row["collaborator"].casefold())
        return ReportDataset(
            provider_key=self.key,
            title="Acessos semanais dos subordinados diretos",
            columns=("registration", "collaborator", "recordedOpens", "applications"),
            rows=rows,
            meta={
                "managerRegistration": registration,
                "managerCoreUserId": manager_id,
                "managerEmail": manager_email.strip().lower(),
                "weekStart": monday,
                "weekEndExclusive": end_exclusive,
                "timezone": "America/Sao_Paulo",
                "directOnly": True,
                "directMemberCount": len(rows),
            },
        )

    def render_email(self, dataset: ReportDataset) -> EmailPayload:
        if dataset.provider_key != self.key or dataset.meta.get("directOnly") is not True:
            raise ValueError("Somente relatório direto pode ser enviado.")
        monday = date.fromisoformat(str(dataset.meta["weekStart"]))
        sunday = monday + timedelta(days=6)
        period = f"{monday:%d/%m/%Y} a {sunday:%d/%m/%Y}"

        cells = []
        for row in dataset.rows:
            count = row["recordedOpens"]
            cells.append([
                str(row["collaborator"]),
                "Indisponível" if count is None else str(count),
                str(row["applications"]),
            ])
        body = (
            '<p style="margin:0 0 14px;font-size:14px;">'
            'Resumo dos <strong>subordinados diretos</strong> da sua equipe '
            f'no período <strong>{html.escape(period)}</strong>.</p>'
        )
        if cells:
            body += ReportEmailBrandLayoutService.data_table_html(
                headers=["Colaborador", "Aberturas registradas", "Ferramentas"],
                rows=cells,
            )
        else:
            body += "<p>Não há subordinados diretos ativos nesta equipe.</p>"
        body += (
            f'<p style="font-size:12px;color:{GRAY_600};margin-top:14px;">'
            "Aberturas são eventos registrados, não tempo de uso ou presença. "
            "“Indisponível” significa que não há dados autorizados para apresentação; "
            "zero evento não comprova ausência de acesso.</p>"
        )
        return EmailPayload(
            subject=f"Minha Delpi | Acessos semanais da equipe direta | {period}",
            html_body=ReportEmailBrandLayoutService.wrap(
                title="Acessos da equipe direta",
                subtitle=f"Delpi Reports · {period}",
                body_html=body,
            ),
        )
