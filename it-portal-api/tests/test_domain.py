from datetime import date

import pytest

from it_portal_app.domain.action_plans import (
    ALLOWED_TRANSITIONS,
    build_action_plan_fields,
    ensure_transition,
    is_overdue,
)
from it_portal_app.domain.errors import ConflictError, ValidationError
from it_portal_app.domain.notes import build_note_body
from it_portal_app.domain.secret_guard import contains_secret
from it_portal_app.domain.servers import build_server_fields, diff_fields

from tests.conftest import server_payload


def test_server_fields_normalize_hostname_and_ip():
    fields = build_server_fields(
        server_payload(hostname="  SRV-ERP-01.Delpi.Local. ", ip_address=" 10.0.0.5 ")
    )
    assert fields.hostname == "srv-erp-01.delpi.local"
    assert fields.ip_address == "10.0.0.5"


def test_server_ip_is_optional_and_accepts_ipv6():
    assert build_server_fields(server_payload(ip_address="")).ip_address is None
    assert build_server_fields(server_payload(ip_address="fe80::1")).ip_address == "fe80::1"


@pytest.mark.parametrize(
    "overrides, field",
    [
        ({"hostname": "srv_erp"}, "hostname"),
        ({"hostname": "-srv"}, "hostname"),
        ({"hostname": "a" * 64}, "hostname"),
        ({"ip_address": "999.1.1.1"}, "ip_address"),
        ({"name": "  "}, "name"),
        ({"unit_code": "03"}, "unit_code"),
        ({"environment": "prod"}, "environment"),
        ({"criticality": "extreme"}, "criticality"),
        ({"administrative_status": "online"}, "administrative_status"),
        ({"server_type": "container"}, "server_type"),
    ],
)
def test_server_validation_reports_field(overrides, field):
    with pytest.raises(ValidationError) as exc:
        build_server_fields(server_payload(**overrides))
    assert exc.value.code == "invalid_server"
    assert field in exc.value.details["fields"]


def test_server_validation_reports_all_missing_required_fields():
    with pytest.raises(ValidationError) as exc:
        build_server_fields({})
    assert set(exc.value.details["fields"]) >= {
        "name",
        "hostname",
        "unit_code",
        "environment",
        "server_type",
        "criticality",
        "administrative_status",
    }


@pytest.mark.parametrize(
    "text",
    [
        "senha: Sup3rS3cret!",
        "password=hunter2hunter2",
        "token = abcd1234efgh",
        "-----BEGIN RSA PRIVATE KEY-----",
        "AKIAABCDEFGHIJKLMNOP",
        "conecte em https://admin:pa55word@srv-erp-01",
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.c2lnbmF0dXJlLXZhbHVl",
    ],
)
def test_secret_guard_detects_credentials(text):
    assert contains_secret(text)


@pytest.mark.parametrize(
    "text",
    [
        "Senha do serviço fica no cofre corporativo.",
        "Trocar token de integração na próxima janela.",
        "Reiniciar o serviço após atualização do Windows.",
    ],
)
def test_secret_guard_allows_operational_text(text):
    assert not contains_secret(text)


def test_secret_rejected_in_note_and_description():
    with pytest.raises(ValidationError) as exc:
        build_note_body("acesso root senha: P@ssw0rd123")
    assert exc.value.code == "secret_not_allowed"
    with pytest.raises(ValidationError):
        build_server_fields(server_payload(description="password: abcdefgh"))


def test_note_requires_text():
    with pytest.raises(ValidationError):
        build_note_body("   ")


def test_action_plan_fields_validation():
    fields = build_action_plan_fields(
        {"title": "Atualizar SO", "priority": "high", "due_date": "2026-12-01"}
    )
    assert fields.due_date == date(2026, 12, 1)
    with pytest.raises(ValidationError) as exc:
        build_action_plan_fields({"title": "", "priority": "x", "due_date": "01/12/2026"})
    assert set(exc.value.details["fields"]) == {"title", "priority", "due_date"}


def test_status_transitions():
    ensure_transition("pending", "in_progress")
    ensure_transition("done", "in_progress")
    with pytest.raises(ConflictError):
        ensure_transition("done", "cancelled")
    with pytest.raises(ConflictError):
        ensure_transition("pending", "pending")
    with pytest.raises(ValidationError):
        ensure_transition("pending", "archived")
    assert all(current not in targets for current, targets in ALLOWED_TRANSITIONS.items())


def test_overdue_only_for_open_plans_before_today():
    today = date(2026, 11, 10)
    assert is_overdue("pending", date(2026, 11, 9), today)
    assert not is_overdue("pending", today, today)
    assert not is_overdue("done", date(2026, 1, 1), today)
    assert not is_overdue("in_progress", None, today)


def test_diff_fields_lists_only_changes():
    assert diff_fields({"a": 1, "b": 2}, {"a": 1, "b": 3}, ("a", "b")) == {
        "b": {"from": 2, "to": 3}
    }
