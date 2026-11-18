"""GLPI #887: provider scope, consent redaction, recipient policy and gate."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.domain.services.reports.direct_weekly_team_delivery_policy import (
    ensure_manager_is_sole_recipient,
)
from app.domain.services.reports.providers.team_direct_app_opens_weekly_provider import (
    DirectTeamUsageWeeklyProvider,
)
from app.domain.services.reports.report_types import ReportDataset


MANAGER_ID = str(uuid4())
REPORT = {
    "source": "app_usage_events",
    "managerRegistration": "20001",
    "includeIndirect": False,
    "directOnly": True,
    "timezone": "America/Sao_Paulo",
    "weekStart": "2026-11-09",
    "weekEndExclusive": "2026-11-16",
    "teamCount": 2,
    "recipient": {"userId": MANAGER_ID, "email": "Gestor@Delpi.com.br"},
    "members": [
        {
            "registration": "00001",
            "fullName": "PESSOA <TESTE>",
            "relationship": "direct",
            "usageStatus": "recorded_opens",
            "totalRecordedOpens": 3,
            "apps": [{"appName": "Portal RH", "recordedOpens": 3}],
        },
        {
            "registration": "00002",
            "fullName": "SEM CONSENTIMENTO",
            "relationship": "direct",
            "usageStatus": "consent_not_granted",
            "totalRecordedOpens": None,
            "apps": [],
        },
    ],
}


def _provider(payload=REPORT):
    class _Response:
        def raise_for_status(self):
            return None

        def json(self):
            return payload

    class _Requests:
        def __init__(self):
            self.calls = []

        def get(self, url, **kwargs):
            self.calls.append((url, kwargs))
            return _Response()

    transport = _Requests()
    provider = DirectTeamUsageWeeklyProvider(
        core_base_url="http://core-api:8000",
        service_token="special-token",
        session=transport,
    )
    return provider, transport


def test_provider_uses_fixed_direct_endpoint_and_masks_nonconsented_employee():
    provider, transport = _provider()
    dataset = provider.collect({"managerRegistration": "20001"})
    assert dataset.row_count == 2
    assert dataset.meta["directOnly"] is True
    assert dataset.meta["managerCoreUserId"] == MANAGER_ID
    assert dataset.meta["managerEmail"] == "gestor@delpi.com.br"
    assert dataset.rows[0]["recordedOpens"] == 3
    assert dataset.rows[1]["recordedOpens"] is None
    assert dataset.rows[1]["applications"] == "Dados indisponíveis"
    url, options = transport.calls[0]
    assert url.endswith("/managers/20001/reports/direct-weekly-opens")
    assert options["headers"] == {"X-Delpi-Service-Token": "special-token"}
    assert "include_indirect" not in options["params"] if options["params"] else True

    email = provider.render_email(dataset)
    assert "subordinados diretos" in email.html_body
    assert "Portal RH: 3" in email.html_body
    assert "&lt;TESTE&gt;" in email.html_body
    assert "SEM CONSENTIMENTO" in email.html_body
    assert "Indisponível" in email.html_body
    assert "consent_not_granted" not in email.html_body
    assert "Gestor@Delpi.com.br" not in email.html_body


def test_provider_rejects_scope_override_before_transport():
    provider, transport = _provider()
    with pytest.raises(ValueError, match="não permitidos"):
        provider.collect({"managerRegistration": "20001", "includeIndirect": True})
    assert transport.calls == []


def test_provider_rejects_indirect_member_even_with_core_claiming_direct():
    import copy

    payload = copy.deepcopy(REPORT)
    payload["members"][0]["relationship"] = "indirect"
    provider, _ = _provider(payload)
    with pytest.raises(ValueError, match="fora do escopo"):
        provider.collect({"managerRegistration": "20001"})


def test_provider_rejects_nonconsented_leak():
    import copy

    payload = copy.deepcopy(REPORT)
    payload["members"][1]["apps"] = [{"appName": "Reports", "recordedOpens": 1}]
    provider, _ = _provider(payload)
    with pytest.raises(ValueError, match="não autorizados"):
        provider.collect({"managerRegistration": "20001"})


def test_provider_rejects_mismatched_manager_registration():
    import copy

    payload = copy.deepcopy(REPORT)
    payload["managerRegistration"] = "20002"
    provider, _ = _provider(payload)
    with pytest.raises(ValueError, match="escopo"):
        provider.collect({"managerRegistration": "20001"})


def test_solo_manager_recipient_policy_rejects_all_other_accounts():
    provider, _ = _provider()
    dataset = provider.collect({"managerRegistration": "20001"})
    valid = [{"userId": MANAGER_ID, "email": "gestor@delpi.com.br"}]
    ensure_manager_is_sole_recipient(recipients=valid, dataset=dataset)

    for invalid in [
        [],
        valid + valid,
        [{"userId": MANAGER_ID, "email": "outro@delpi.com.br"}],
        [{"userId": str(uuid4()), "email": "gestor@delpi.com.br"}],
        [{"userId": MANAGER_ID, "email": "g***@delpi.com.br"}],
    ]:
        with pytest.raises(ValueError):
            ensure_manager_is_sole_recipient(recipients=invalid, dataset=dataset)


def test_recipient_policy_rejects_indirect_meta():
    dataset = ReportDataset(
        provider_key="team_direct_app_opens_weekly",
        title="test", columns=(), rows=(),
        meta={
            "managerRegistration": "20001",
            "managerCoreUserId": MANAGER_ID,
            "managerEmail": "gestor@delpi.com.br",
            "directOnly": False,
        },
    )
    with pytest.raises(ValueError, match="não atestados"):
        ensure_manager_is_sole_recipient(
            recipients=[{"userId": MANAGER_ID, "email": "gestor@delpi.com.br"}],
            dataset=dataset,
        )


def test_run_fails_before_any_graph_send_when_disabled(monkeypatch):
    from unittest.mock import MagicMock
    from app.application.use_cases.reports.run_report_definition_use_case import (
        RunReportDefinitionUseCase,
    )
    from app.application.use_cases.reports import run_report_definition_use_case as run_module

    monkeypatch.setattr(
        run_module.settings,
        "REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED",
        False,
    )
    repo = MagicMock()
    repo.get_definition.return_value = {
        "active": True,
        "providerKey": "team_direct_app_opens_weekly",
        "params": {"managerRegistration": "20001"},
    }
    repo.list_active_recipients.return_value = [
        {"userId": MANAGER_ID, "email": "gestor@delpi.com.br"}
    ]
    registry = MagicMock()
    mail = MagicMock()
    use_case = RunReportDefinitionUseCase(repo, registry, mail)
    with pytest.raises(ValueError, match="desabilitado"):
        use_case.execute(definition_id=str(uuid4()))
    repo.create_run.assert_not_called()
    mail.send_mail_to.assert_not_called()
