"""GLPI #887: previous completed-week app openings for verified RH team members.

No automatic mail, self-service supervisor access or identity inference.
Recorded events are telemetry, not a precise count of human sessions.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


# Core image uses python:3.11-slim; tzdata may be absent at runtime.
# Brazil has observed UTC-3 without DST since 2019. This safe fallback
# avoids blocking the API on hosts with no OS time zone database.
try:
    REPORT_TIMEZONE = ZoneInfo("America/Sao_Paulo")
except ZoneInfoNotFoundError:
    REPORT_TIMEZONE = timezone(timedelta(hours=-3))
REPORT_TIMEZONE_LABEL = "America/Sao_Paulo"
MAX_TEAM_MEMBERS = 500
MAX_WEEK_AGE_DAYS = 90


def week_window(
    requested_monday: str | None,
    *,
    now_utc: datetime | None = None,
) -> tuple[date, datetime, datetime]:
    """Completed Sao Paulo calendar week to a [start, end) naive UTC window."""
    clock = now_utc or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        raise ValueError("Relógio da apuração deve conter fuso horário.")
    local_today = clock.astimezone(REPORT_TIMEZONE).date()
    current_monday = local_today - timedelta(days=local_today.weekday())

    if requested_monday is None:
        monday = current_monday - timedelta(days=7)
    else:
        try:
            monday = date.fromisoformat(requested_monday)
        except (TypeError, ValueError) as exc:
            raise ValueError("week_start deve ser AAAA-MM-DD.") from exc
        if monday.isoformat() != requested_monday:
            raise ValueError("week_start deve ser AAAA-MM-DD.")

    if monday.weekday() != 0:
        raise ValueError("week_start deve ser uma segunda-feira.")
    if monday >= current_monday:
        raise ValueError("Somente semanas completas e encerradas podem ser apuradas.")
    if (local_today - monday).days > MAX_WEEK_AGE_DAYS:
        raise ValueError("week_start excede a janela permitida de 90 dias.")

    local_start = datetime.combine(monday, time.min, tzinfo=REPORT_TIMEZONE)
    local_end = datetime.combine(monday + timedelta(days=7), time.min, tzinfo=REPORT_TIMEZONE)
    return (
        monday,
        local_start.astimezone(timezone.utc).replace(tzinfo=None),
        local_end.astimezone(timezone.utc).replace(tzinfo=None),
    )


class OrganizationWeeklyUsageService:
    """Combine authoritative HR mappings, live consent and grouped opening events."""

    def __init__(self, team_service, usage_repository):
        self.team_service = team_service
        self.usage_repository = usage_repository

    def get_weekly_report(
        self,
        manager_registration: str,
        *,
        week_start: str | None = None,
        include_indirect: bool = True,
        details: bool = False,
        now_utc: datetime | None = None,
    ) -> dict:
        monday, since, until = week_window(week_start, now_utc=now_utc)
        team = self.team_service.get_team(
            manager_registration,
            include_indirect=include_indirect,
            include_inactive=False,
        )
        members = team["members"]
        if len(members) > MAX_TEAM_MEMBERS:
            raise ValueError("Equipe excede limite de 500 colaboradores.")

        # Only explicit verified HR-to-Core mapping can authorize inclusion.
        # Name/email suggestions from the admin reconciliation preview are ignored.
        mapped = {}
        for member in members:
            raw_id = member.get("coreUserId")
            if member.get("identityStatus") != "mapped" or not raw_id:
                continue
            uid = UUID(str(raw_id))
            if uid in mapped:
                raise ValueError("Vínculo Core repetido na hierarquia RH.")
            mapped[uid] = member

        eligible_ids = self.usage_repository.consented_active_user_ids(set(mapped))
        if not eligible_ids.issubset(set(mapped)):
            raise ValueError("Consentimento fora da equipe verificada.")

        grouped_opens = self.usage_repository.app_opens(
            user_ids=eligible_ids,
            since=since,
            until=until,
        ) if eligible_ids else []

        # Session durations are separate from open events. Query only for
        # consented verified identities and only when nominal detail is asked.
        durations_by_user_app = {}
        if details and eligible_ids:
            for item in self.usage_repository.app_session_durations(
                user_ids=eligible_ids, since=since, until=until,
            ):
                user_id = UUID(str(item["userId"]))
                if user_id not in eligible_ids:
                    raise ValueError("Duração retornada para usuário não autorizado.")
                app_id = str(item["appId"])
                count = int(item["sessionCount"])
                seconds = int(item["totalDurationSeconds"])
                if not app_id or count <= 0 or seconds < count:
                    raise ValueError("Métricas de duração inválidas.")
                key = (user_id, app_id)
                if key in durations_by_user_app:
                    raise ValueError("Sessões de aplicativo duplicadas.")
                durations_by_user_app[key] = (count, seconds)

        opens_by_user = defaultdict(list)
        for item in grouped_opens:
            user_id = UUID(str(item["userId"]))
            if user_id not in eligible_ids:
                raise ValueError("Uso retornado para usuário não autorizado.")
            count = int(item["count"])
            if count <= 0:
                continue
            opens_by_user[user_id].append({
                "appId": item["appId"],
                "appName": item["appName"],
                "recordedOpens": count,
            })

        counts = {
            "verifiedMapped": len(mapped),
            "unmapped": len(members) - len(mapped),
            "consentGranted": len(eligible_ids),
            "consentNotGranted": len(mapped) - len(eligible_ids),
            "withRecordedOpens": 0,
            "withoutRecordedOpens": 0,
        }
        total = 0
        rows = []
        for member in members:
            uid = (
                UUID(str(member["coreUserId"]))
                if member.get("identityStatus") == "mapped" and member.get("coreUserId")
                else None
            )
            if uid is None:
                status, apps, opens = "unmapped", [], None
            elif uid not in eligible_ids:
                status, apps, opens = "consent_not_granted", [], None
            else:
                apps = sorted(
                    opens_by_user[uid],
                    key=lambda x: (-x["recordedOpens"], x["appName"], x["appId"]),
                )
                if details:
                    apps = [
                        {
                            **app,
                            "recordedSessions": durations_by_user_app.get(
                                (uid, app["appId"]), (0, 0)
                            )[0],
                            "totalDurationSeconds": durations_by_user_app.get(
                                (uid, app["appId"]), (0, 0)
                            )[1],
                            # No persisted sessions => unavailable, NEVER zero.
                            "avgSessionSeconds": (
                                round(
                                    durations_by_user_app[(uid, app["appId"])][1]
                                    / durations_by_user_app[(uid, app["appId"])][0]
                                )
                                if (uid, app["appId"]) in durations_by_user_app
                                else None
                            ),
                        }
                        for app in apps
                    ]
                opens = sum(item["recordedOpens"] for item in apps)
                if opens:
                    status = "recorded_opens"
                    counts["withRecordedOpens"] += 1
                else:
                    status = "no_recorded_opens"
                    counts["withoutRecordedOpens"] += 1
                total += opens
            if details:
                rows.append({
                    "registration": member["registration"],
                    "fullName": member["fullName"],
                    "branchCode": member["branchCode"],
                    "relationship": member["relationship"],
                    "usageStatus": status,
                    # None is deliberately different from zero.
                    "totalRecordedOpens": opens,
                    "apps": apps,
                })

        payload = {
            "source": "app_usage_events",
            "managerRegistration": manager_registration,
            "includeIndirect": bool(include_indirect),
            "weekStart": monday.isoformat(),
            "weekEndExclusive": (monday + timedelta(days=7)).isoformat(),
            "timezone": REPORT_TIMEZONE_LABEL,
            "teamCount": len(members),
            **counts,
            "totalRecordedOpens": total,
            "readOnly": True,
            "reportSent": False,
            "note": (
                "Contagens refletem eventos registrados de abertura de apps, não "
                "visitas únicas nem tempo de uso. Sem vínculo/consentimento não "
                "significa sem acesso; zero evento não comprova ausência de uso."
            ),
        }
        if details:
            payload["members"] = rows
        return payload
