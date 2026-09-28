"""HELPDESK-IDENTITY-001B — canonical first/last name vs GLPI firstname/realname.

Runtime evidence proved the user-scoped OAuth authority cannot write
Administration/User names (GLPI_SELF_PROFILE_WRITE_NOT_AUTHORIZED). The
reconcile therefore detects drift and reports deferred_write_authority with
ZERO PATCH attempts. Covers: noop, deferred drift, read failures, skip paths,
memo behavior, access trigger, no client-supplied profile, no leakage.
"""

import logging
from types import SimpleNamespace

from helpdesk_app.application.profile_sync_service import (
    DEFERRED_WRITE_AUTHORITY,
    FAILED,
    FAILED_FORBIDDEN,
    FAILED_UNAVAILABLE,
    NOOP,
    SKIPPED_NO_CANONICAL_NAME,
    SKIPPED_NO_GLPI_USER,
    ProfileSyncService,
)
from helpdesk_app.domain.errors import GlpiForbidden, GlpiUnavailable
from helpdesk_app.domain.models import Actor

from tests.conftest import FakeGlpi, auth_headers, build_client, link


def _glpi_user(glpi: FakeGlpi, user_id=15, firstname="", realname="", username="ana@delpi.com.br"):
    glpi.session_uid = user_id
    glpi.user_profiles[int(user_id)] = SimpleNamespace(
        username=username,
        firstname=firstname,
        realname=realname,
        emails=("ana@delpi.com.br",),
    )
    return user_id


def test_session_bootstrap_reports_deferred_on_drift():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
    )
    assert response.status_code == 200
    assert response.json() == {"linked": True, "profile_sync": DEFERRED_WRITE_AUTHORITY}
    # Drift detected, authority insufficient — ZERO writes, GLPI untouched.
    assert glpi.profile_updates == []
    assert glpi.user_profiles[15].firstname == ""
    assert glpi.user_profiles[15].realname == ""


def test_partial_name_drift_is_deferred_not_written():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="Ana", realname="")
    client, glpi = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
    )
    assert response.json()["profile_sync"] == DEFERRED_WRITE_AUTHORITY
    assert glpi.profile_updates == []
    assert glpi.user_profiles[15].realname == ""


def test_changed_canonical_name_deferred_zero_patch():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="Ana", realname="Silva")
    client, glpi = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-given-name": "Ana Beatriz", "x-family-name": "Silva Souza"},
    )
    assert response.json()["profile_sync"] == DEFERRED_WRITE_AUTHORITY
    assert glpi.profile_updates == []
    assert glpi.user_profiles[15].firstname == "Ana"


def test_synced_profile_is_noop():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="Ana", realname="Silva")
    client, glpi = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
    )
    assert response.json()["profile_sync"] == NOOP
    assert glpi.profile_updates == []


def test_deferred_outcome_is_memoized_zero_provider_reads_in_window():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi)
    link(client)
    headers = {**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"}
    assert client.get("/auth/glpi/session", headers=headers).json()["profile_sync"] == DEFERRED_WRITE_AUTHORITY
    calls_after_first = glpi.calls
    assert client.get("/auth/glpi/session", headers=headers).json()["profile_sync"] == DEFERRED_WRITE_AUTHORITY
    # Settled detection memoized — no repeated provider reads, still zero PATCH.
    assert glpi.calls == calls_after_first
    assert glpi.profile_updates == []


def test_mapping_stable_and_no_duplicate_user_after_name_change():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="Ana", realname="Silva", user_id=42)
    client, glpi = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-given-name": "Ana Maria", "x-family-name": "Silva"},
    )
    assert response.json()["profile_sync"] == DEFERRED_WRITE_AUTHORITY
    assert glpi.profile_updates == []
    assert set(glpi.user_profiles) == {42}


def test_empty_canonical_value_never_erases_provider_field():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="Ana", realname="Silva")
    client, glpi = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-given-name": "Ana Maria"},
    )
    assert response.json()["profile_sync"] == DEFERRED_WRITE_AUTHORITY
    assert glpi.profile_updates == []
    assert glpi.user_profiles[15].realname == "Silva"


def test_no_canonical_split_means_skip_not_blank():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-name": "Ana Silva"},
    )
    assert response.json()["profile_sync"] == SKIPPED_NO_CANONICAL_NAME
    assert glpi.profile_updates == []


def test_unlinked_session_skips_sync():
    glpi = FakeGlpi()
    client, _ = build_client(glpi)
    response = client.get("/auth/glpi/session", headers=auth_headers())
    assert response.json() == {"linked": False}
    assert glpi.profile_updates == []


def test_session_without_glpi_user_is_skipped():
    glpi = FakeGlpi()
    glpi.session_uid = None
    client, _ = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
    )
    assert response.json()["profile_sync"] == SKIPPED_NO_GLPI_USER


def test_provider_forbidden_read_is_fail_closed():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    glpi.get_user_error = GlpiForbidden("negado")
    client, _ = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
    )
    assert response.status_code == 200
    assert response.json()["linked"] is True
    assert response.json()["profile_sync"] == FAILED_FORBIDDEN


def test_provider_unavailable_is_fail_closed():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    glpi.get_user_error = GlpiUnavailable("fora")
    client, _ = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
    )
    assert response.json()["profile_sync"] == FAILED_UNAVAILABLE


def test_request_body_cannot_supply_profile():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi)
    link(client)
    response = client.request(
        "GET",
        "/auth/glpi/session",
        params={"firstname": "Hacker", "realname": "X"},
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
        json={"firstname": "Hacker", "realname": "X", "user_id": 2},
    )
    assert response.json()["profile_sync"] == DEFERRED_WRITE_AUTHORITY
    assert glpi.profile_updates == []
    # Provider state untouched — injection attempt changed nothing.
    assert glpi.user_profiles[15].firstname == ""
    assert glpi.user_profiles[15].realname == ""


def test_response_and_payload_carry_no_tokens():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
    )
    body = response.json()
    assert set(body) == {"linked", "profile_sync"}
    assert glpi.profile_updates == []


def test_logs_contain_no_name_values_or_tokens(caplog):
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, _ = build_client(glpi)
    link(client)
    with caplog.at_level(logging.WARNING, logger="helpdesk.profile_sync"):
        client.get(
            "/auth/glpi/session",
            headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
        )
    text = caplog.text
    assert "deferred_write_authority" in text
    for leaked in ("Ana", "Silva", "access-a", "Bearer", "good-code"):
        assert leaked not in text


def test_direct_service_call_reports_each_outcome():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi)
    link(client)
    tick = [0.0]
    sync = ProfileSyncService(glpi, client.app.state.oauth, now=lambda: tick[0])
    actor = Actor(subject="user-a", email="ana@delpi.com.br", first_name="Ana", last_name="Silva")

    assert sync.ensure_profile(actor) == DEFERRED_WRITE_AUTHORITY
    # Settled detection memoized — provider untouched in-window.
    calls_after = glpi.calls
    assert sync.ensure_profile(actor) == DEFERRED_WRITE_AUTHORITY
    assert glpi.calls == calls_after
    assert glpi.profile_updates == []

    # Provider read failure after the memo window surfaces distinctly.
    glpi.get_user_error = RuntimeError("boom")
    tick[0] += 3700.0
    assert sync.ensure_profile(actor) == FAILED

    # Provider-side drift resolution re-reads as NOOP once observable.
    glpi.get_user_error = None
    glpi.user_profiles[15].firstname = "Ana"
    glpi.user_profiles[15].realname = "Silva"
    tick[0] += 3700.0
    assert sync.ensure_profile(actor) == NOOP


def test_reconcile_runs_on_any_authenticated_helpdesk_access():
    """The real entry trigger: the MFE loads /tickets on page entry — it never
    calls /auth/glpi/session. require_actor must fire the drift check."""
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi)
    link(client)
    response = client.get(
        "/tickets",
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
    )
    assert response.status_code == 200
    assert glpi.profile_updates == []  # bounded check, zero writes
    # The drift check DID run (session_user_id + get_user calls happened).
    assert glpi.calls >= 3


def test_reconcile_failure_does_not_break_ticket_access():
    """AUTHENTICATION_SUCCESS must never depend on profile sync succeeding."""
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    glpi.get_user_error = GlpiForbidden("negado")
    client, _ = build_client(glpi)
    link(client)
    response = client.get(
        "/tickets",
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
    )
    assert response.status_code == 200
    assert response.json()["items"]


def test_sync_not_retried_on_every_request_while_linked_outcome_pending():
    """Two consecutive requests: only the first reconcile hits the provider
    (skipped states use a short retry window, not per-request)."""
    glpi = FakeGlpi()  # session_uid=None → skipped_no_glpi_user
    client, glpi = build_client(glpi)
    link(client)
    headers = {**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"}
    client.get("/tickets", headers=headers)
    calls_after_first = glpi.calls
    client.get("/tickets", headers=headers)
    # Second request: reconcile memo-hit → no extra session_user_id call;
    # +1 call is the list_tickets itself.
    assert glpi.calls == calls_after_first + 1


def test_ticket_flows_do_not_regress():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="Ana", realname="Silva")
    client, _ = build_client(glpi)
    link(client)
    response = client.get("/tickets", headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["items"]
