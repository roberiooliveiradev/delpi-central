"""HELPDESK-IDENTITY-001B/002A — canonical first/last name vs GLPI profile.

Runtime evidence proved the user-scoped OAuth authority cannot write
Administration/User names (GLPI_SELF_PROFILE_WRITE_NOT_AUTHORIZED). Without a
technical writer, drift reports deferred_write_authority with ZERO writes.
IDENTITY-002A adds the narrow ProfileSyncWriterPort (dedicated technical
principal, names-only write + authoritative reread) behind a feature flag,
and per-Keycloak-session cadence keyed on (subject, sid) — never token hash.
"""

import logging
from types import SimpleNamespace

from helpdesk_app.application.profile_sync_service import (
    DEFERRED_WRITE_AUTHORITY,
    FAILED,
    FAILED_FORBIDDEN,
    FAILED_UNAVAILABLE,
    FAILED_VERIFICATION,
    FAILED_WRITE,
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

    # Provider read failure after the terminal memo window surfaces distinctly.
    glpi.get_user_error = RuntimeError("boom")
    tick[0] += 43300.0
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


# ---------------------------------------------------------------------------
# HELPDESK-IDENTITY-002A — technical writer (feature-flagged, names-only).
# ---------------------------------------------------------------------------


def test_parity_with_writer_stays_noop_zero_write():
    """Parity → NOOP even with the technical writer wired — zero writes."""
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="Ana", realname="Silva")
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    headers = {**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"}
    assert client.get("/auth/glpi/session", headers=headers).json()["profile_sync"] == NOOP
    assert glpi.profile_updates == []


def test_drift_with_writer_syncs_only_divergent_firstname():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="Silva")
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    headers = {**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"}
    assert client.get("/auth/glpi/session", headers=headers).json()["profile_sync"] == SYNCED
    # Only the divergent field was sent — realname untouched by the write.
    assert glpi.profile_updates == [(15, "Ana", None)]
    assert glpi.user_profiles[15].firstname == "Ana"
    assert glpi.user_profiles[15].realname == "Silva"


def test_drift_with_writer_syncs_only_divergent_realname():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="Ana", realname="")
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    headers = {**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"}
    assert client.get("/auth/glpi/session", headers=headers).json()["profile_sync"] == SYNCED
    assert glpi.profile_updates == [(15, None, "Silva")]


def test_drift_with_writer_syncs_both_names():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    headers = {**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"}
    assert client.get("/auth/glpi/session", headers=headers).json()["profile_sync"] == SYNCED
    assert glpi.profile_updates == [(15, "Ana", "Silva")]
    assert glpi.user_profiles[15].firstname == "Ana"
    assert glpi.user_profiles[15].realname == "Silva"


def test_writer_target_is_session_user_never_request_supplied_id():
    """TARGET BINDING — body/query/params cannot choose another user_id."""
    glpi = FakeGlpi()
    _glpi_user(glpi, user_id=99, firstname="", realname="", username="victim@x")
    _glpi_user(glpi, user_id=15, firstname="", realname="")
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    response = client.request(
        "GET",
        "/auth/glpi/session",
        params={"user_id": 99},
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
        json={"user_id": 99},
    )
    assert response.json()["profile_sync"] == SYNCED
    # Write hit ONLY the session-resolved user 15 — never the injected 99.
    assert glpi.profile_updates == [(15, "Ana", "Silva")]
    assert glpi.user_profiles[99].firstname == ""


def test_request_cannot_inject_provider_fields():
    """The writer body carries only firstname/realname — nothing else."""
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    response = client.request(
        "GET",
        "/auth/glpi/session",
        params={"email": "evil@x", "is_active": 0, "password": "x"},
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
        json={"email": "evil@x", "profiles_id": 4, "entities_id": 0},
    )
    assert response.json()["profile_sync"] == SYNCED
    # Exactly one write, exactly two name fields — no extra keys possible.
    assert len(glpi.profile_updates) == 1
    assert glpi.profile_updates[0] == (15, "Ana", "Silva")


def test_new_access_token_same_sid_does_not_reconcile_again():
    """Token refresh inside a session must not split the semantic session."""
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="Ana", realname="Silva")
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    headers = {
        **auth_headers(),
        "x-given-name": "Ana",
        "x-family-name": "Silva",
        "x-sid": "kc-session-1",
    }
    assert client.get("/auth/glpi/session", headers=headers).json()["profile_sync"] == NOOP
    calls_after_first = glpi.calls
    assert client.get("/auth/glpi/session", headers=headers).json()["profile_sync"] == NOOP
    assert glpi.calls == calls_after_first  # memoized — no new provider reads


def test_new_sid_triggers_fresh_reconciliation():
    """A new Keycloak session (new login) performs a fresh bounded check."""
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="Ana", realname="Silva")
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    base = {**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"}
    assert client.get("/auth/glpi/session", headers={**base, "x-sid": "s1"}).json()["profile_sync"] == NOOP
    calls_after_first = glpi.calls
    assert client.get("/auth/glpi/session", headers={**base, "x-sid": "s2"}).json()["profile_sync"] == NOOP
    assert glpi.calls > calls_after_first  # new session → provider re-read


def test_same_sid_changed_canonical_profile_reconciles():
    """Name change mid-session: fingerprint mismatch → fresh reconcile."""
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="Ana", realname="Silva")
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    base = {**auth_headers(), "x-sid": "kc-session-1"}
    h1 = {**base, "x-given-name": "Ana", "x-family-name": "Silva"}
    assert client.get("/auth/glpi/session", headers=h1).json()["profile_sync"] == NOOP
    # Canonical identity changed → drift → technical write → verify.
    h2 = {**base, "x-given-name": "Ana Beatriz", "x-family-name": "Silva"}
    assert client.get("/auth/glpi/session", headers=h2).json()["profile_sync"] == SYNCED
    assert glpi.profile_updates == [(15, "Ana Beatriz", None)]


def test_writer_403_is_failed_forbidden_fail_closed():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    glpi.update_profile_error = GlpiForbidden("sem direito")
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    headers = {**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"}
    response = client.get("/auth/glpi/session", headers=headers)
    assert response.status_code == 200
    assert response.json()["profile_sync"] == FAILED_FORBIDDEN
    assert glpi.user_profiles[15].firstname == ""


def test_writer_unavailable_is_failed_unavailable_fail_closed():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    glpi.update_profile_error = GlpiUnavailable("fora")
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    headers = {**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"}
    response = client.get("/auth/glpi/session", headers=headers)
    assert response.status_code == 200
    assert response.json()["profile_sync"] == FAILED_UNAVAILABLE


def test_writer_generic_error_is_failed_write():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    glpi.update_profile_error = RuntimeError("boom")
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    headers = {**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"}
    assert client.get("/auth/glpi/session", headers=headers).json()["profile_sync"] == FAILED_WRITE


def test_write_2xx_but_reread_diverges_is_failed_verification():
    """Provider accepts the write but silently ignores it → NOT synced."""
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    glpi.profile_update_applies = False  # write lands 2xx, row unchanged
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    headers = {**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"}
    assert client.get("/auth/glpi/session", headers=headers).json()["profile_sync"] == FAILED_VERIFICATION
    assert len(glpi.profile_updates) == 1


def test_synced_session_performs_zero_writes_on_repeat():
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    headers = {
        **auth_headers(),
        "x-given-name": "Ana",
        "x-family-name": "Silva",
        "x-sid": "kc-session-1",
    }
    assert client.get("/auth/glpi/session", headers=headers).json()["profile_sync"] == SYNCED
    assert len(glpi.profile_updates) == 1
    calls_after_sync = glpi.calls
    # Repeat access inside the same session: memoized synced, zero writes/reads.
    assert client.get("/auth/glpi/session", headers=headers).json()["profile_sync"] == SYNCED
    assert glpi.calls == calls_after_sync
    assert len(glpi.profile_updates) == 1


def test_helpdesk_access_survives_writer_failure():
    """Sync failure must never become an authentication failure."""
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    glpi.update_profile_error = GlpiForbidden("sem direito")
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    response = client.get(
        "/tickets",
        headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
    )
    assert response.status_code == 200
    assert response.json()["items"]


def test_technical_write_logs_no_names_or_credentials(caplog):
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    with caplog.at_level(logging.INFO, logger="helpdesk.profile_sync"):
        client.get(
            "/auth/glpi/session",
            headers={**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"},
        )
    text = caplog.text
    assert "synced" in text or "system/profile-sync" in text
    for leaked in ("Ana", "Silva", "access-a", "Bearer", "user_token", "App-Token"):
        assert leaked not in text


def test_writer_absent_keeps_001b_deferred_semantics():
    """001B contract intact: writer=None → deferred, zero writes."""
    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi)  # no writer — feature flag OFF path
    link(client)
    headers = {**auth_headers(), "x-given-name": "Ana", "x-family-name": "Silva"}
    assert client.get("/auth/glpi/session", headers=headers).json()["profile_sync"] == DEFERRED_WRITE_AUTHORITY
    assert glpi.profile_updates == []


def test_concurrent_ensure_profile_converges_single_write():
    """Two simultaneous reconciles converge — at most convergent writes of
    the same values, never duplicate divergent writes."""
    import threading

    glpi = FakeGlpi()
    _glpi_user(glpi, firstname="", realname="")
    client, glpi = build_client(glpi, sync_writer=True)
    link(client)
    sync = client.app.state.profile_sync
    actor = Actor(
        subject="user-a",
        email="ana@delpi.com.br",
        first_name="Ana",
        last_name="Silva",
        session_id="kc-session-1",
    )
    results = []
    threads = [threading.Thread(target=lambda: results.append(sync.ensure_profile(actor))) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert set(results) <= {SYNCED}
    assert len(glpi.profile_updates) <= 4
    # Converged — final state is parity.
    assert glpi.user_profiles[15].firstname == "Ana"
    assert glpi.user_profiles[15].realname == "Silva"
