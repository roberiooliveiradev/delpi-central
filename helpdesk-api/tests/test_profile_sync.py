"""HELPDESK-IDENTITY-001 — canonical first/last name → GLPI firstname/realname.

Covers: repair on link, changed canonical name, noop, idempotency, stable
mapping, no duplicate user, provider failures, postcondition verification,
no client-supplied profile, no credential leakage.
"""

from types import SimpleNamespace

from helpdesk_app.application.profile_sync_service import (
    FAILED,
    FAILED_FORBIDDEN,
    FAILED_UNAVAILABLE,
    FAILED_VERIFICATION,
    NOOP,
    SKIPPED_NO_CANONICAL_NAME,
    SKIPPED_NO_GLPI_USER,
    SYNCED,
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


def test_session_bootstrap_repairs_missing_names():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
    )
    assert response.status_code == 200
    assert response.json() == {"linked": True, "profile_sync": SYNCED}
    row = glpi.user_profiles[15]
    assert row.firstname == "Ana"
    assert row.realname == "Silva"
    assert glpi.profile_updates == [(15, "Ana", "Silva")]


def test_existing_user_with_partial_name_gets_repaired():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="Ana", realname="")
    client, glpi = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
    )
    assert response.json()["profile_sync"] == SYNCED
    assert glpi.user_profiles[15].realname == "Silva"


def test_changed_canonical_name_updates_glpi():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="Ana", realname="Silva")
    client, glpi = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-given-name": "Ana Beatriz", "x-family-name": "Silva Souza"},
    )
    assert response.json()["profile_sync"] == SYNCED
    assert glpi.user_profiles[15].firstname == "Ana Beatriz"
    assert glpi.user_profiles[15].realname == "Silva Souza"


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


def test_repeated_reconciliation_is_idempotent():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi)
    link(client)
    headers = {**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"}
    assert client.get("/auth/glpi/session", headers=headers).json()["profile_sync"] == SYNCED
    assert client.get("/auth/glpi/session", headers=headers).json()["profile_sync"] == SYNCED
    assert len(glpi.profile_updates) == 1


def test_mapping_stable_and_no_duplicate_user_after_name_change():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="Ana", realname="Silva", user_id=42)
    client, glpi = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-given-name": "Ana Maria", "x-family-name": "Silva"},
    )
    assert response.json()["profile_sync"] == SYNCED
    assert glpi.profile_updates == [(42, "Ana Maria", None)]
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
    assert response.json()["profile_sync"] == SYNCED
    assert glpi.profile_updates == [(15, "Ana Maria", None)]
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


def test_provider_forbidden_write_is_fail_closed():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    glpi.update_profile_error = GlpiForbidden("negado")
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
    glpi.update_profile_error = GlpiUnavailable("fora")
    client, _ = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
    )
    assert response.json()["profile_sync"] == FAILED_UNAVAILABLE


def test_silent_provider_drift_is_detected_by_postcondition():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    glpi.profile_update_applies = False  # 2xx mas o GLPI não persistiu
    client, _ = build_client(glpi)
    link(client)
    response = client.get(
        "/auth/glpi/session",
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
    )
    assert response.json()["profile_sync"] == FAILED_VERIFICATION


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
    assert response.json()["profile_sync"] == SYNCED
    assert glpi.profile_updates == [(15, "Ana", "Silva")]


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
    for _uid, first, last in glpi.profile_updates:
        assert "access" not in str(first).lower()
        assert "Bearer" not in str(last)


def test_direct_service_call_reports_each_outcome():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi)
    link(client)
    tick = [0.0]
    sync = ProfileSyncService(glpi, client.app.state.oauth, now=lambda: tick[0])
    actor = Actor(subject="user-a", email="ana@delpi.com.br", first_name="Ana", last_name="Silva")

    assert sync.ensure_profile(actor) == SYNCED
    # Settled outcome is memoized — provider is not touched again in-window.
    calls_after_sync = glpi.calls
    assert sync.ensure_profile(actor) == SYNCED
    assert glpi.calls == calls_after_sync

    # Provider-side drift after the memo window is reconciled again.
    glpi.user_profiles[15].firstname = "Outra"
    tick[0] += 3700.0
    assert sync.ensure_profile(actor) == SYNCED

    glpi.update_profile_error = RuntimeError("boom")
    glpi.user_profiles[15].firstname = "Outra"
    tick[0] += 3700.0
    assert sync.ensure_profile(actor) == FAILED


def test_reconcile_runs_on_any_authenticated_helpdesk_access():
    """The real entry trigger: the MFE loads /tickets on page entry — it never
    calls /auth/glpi/session. require_actor must fire the reconcile."""
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi)
    link(client)
    response = client.get(
        "/tickets",
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
    )
    assert response.status_code == 200
    assert glpi.profile_updates == [(15, "Ana", "Silva")]
    assert glpi.user_profiles[15].firstname == "Ana"
    assert glpi.user_profiles[15].realname == "Silva"


def test_reconcile_failure_does_not_break_ticket_access():
    """AUTHENTICATION_SUCCESS must never depend on profile sync succeeding."""
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    glpi.update_profile_error = GlpiForbidden("negado")
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
