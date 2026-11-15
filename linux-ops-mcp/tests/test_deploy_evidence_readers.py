"""Offline adapters P2.2b; the GitHub API is fully mocked, no real network."""
import asyncio
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from linux_ops_mcp.deploy_evidence_readers import (
    CorePermissionReader, EvidenceReadError, GithubReleaseReader,
)

SHA = "a" * 40
HEAD = "b" * 40
NOW = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)


def payload(request):
    path = request.url.path
    if path.endswith("/git/ref/heads/main"):
        return {"ref": "refs/heads/main", "object": {"type": "commit", "sha": HEAD}}
    if "/compare/" in path:
        return {"status": "ahead", "base_commit": {"sha": SHA}, "head_commit": {"sha": HEAD}}
    if path.endswith("/actions/runs"):
        return {"total_count": 1, "workflow_runs": [{
            "workflow_id": 777, "id": 123, "run_attempt": 1, "head_sha": SHA,
            "head_branch": "main", "event": "push", "status": "completed", "conclusion": "success",
        }]}
    raise AssertionError(f"unexpected endpoint: {path}")


def reader(handler):
    return GithubReleaseReader(transport=httpx.MockTransport(handler), clock=lambda: NOW)


def run(provider):
    return asyncio.run(provider.read(SHA))


def test_github_success_is_exact_branch_and_commit_without_any_writes():
    requests = []

    def reply(request):
        requests.append(request)
        assert request.method == "GET"
        assert request.url.host == "api.github.com"
        assert request.url.path.startswith("/repos/roberiooliveiradev/delpi-central/")
        return httpx.Response(200, json=payload(request))

    proof = run(reader(reply))
    assert proof.branch == "main" and proof.branch_contains_commit is True
    assert proof.checked_at == NOW and proof.runs[0].workflow_id == 777
    assert len(requests) == 3
    assert requests[-1].url.params["head_sha"] == SHA
    assert requests[-1].url.params["event"] == "push"


def test_access_token_stays_in_headers_and_not_in_exceptions():
    secret = "synthetic-test-token-keep-private"
    observed = []

    def reply(request):
        observed.append(request.headers.get("authorization"))
        return httpx.Response(200, json=payload(request))

    provider = GithubReleaseReader(token=secret, transport=httpx.MockTransport(reply), clock=lambda: NOW)
    run(provider)
    assert observed == [f"Bearer {secret}"] * 3

    def fail(request):
        return httpx.Response(500, text=f"secret={secret}\\nopaque upstream diagnostic")

    with pytest.raises(EvidenceReadError) as exc:
        run(GithubReleaseReader(token=secret, transport=httpx.MockTransport(fail)))
    assert exc.value.code == "GITHUB_UNAVAILABLE" and secret not in str(exc.value)


@pytest.mark.parametrize("sha", ["main", "a" * 39, "A" * 40, "a" * 40 + "-x", "../evil", None])
def test_only_full_lowercase_sha_can_select_git_api_path(sha):
    with pytest.raises(EvidenceReadError, match="COMMIT_SHA_INVALID"):
        asyncio.run(reader(lambda _: (_ for _ in ()).throw(AssertionError("network called"))).read(sha))


@pytest.mark.parametrize("status", [301, 302, 401, 403, 429, 500, 503])
def test_redirects_and_errors_fail_without_following(status):
    with pytest.raises(EvidenceReadError, match="GITHUB_UNAVAILABLE"):
        run(reader(lambda _: httpx.Response(status, headers={"Location": "https://attacker.invalid/"})))


def test_non_json_and_oversize_response_fail_closed():
    with pytest.raises(EvidenceReadError, match="GITHUB_UNAVAILABLE"):
        run(reader(lambda _: httpx.Response(200, headers={"content-type": "text/html"}, text="<secret>")))
    with pytest.raises(EvidenceReadError, match="GITHUB_RESPONSE_TOO_LARGE"):
        run(reader(lambda _: httpx.Response(200, headers={"content-type": "application/json"}, content=b"x" * 256_100)))


@pytest.mark.parametrize("edit,expected", [
    (lambda p: p["object"].update(sha="x" * 40), "GITHUB_REF_UNVERIFIED"),
    (lambda p: p.update(ref="refs/heads/feature"), "GITHUB_REF_UNVERIFIED"),
])
def test_ref_payload_attestation_checks(edit, expected):
    def reply(r):
        p = payload(r)
        if r.url.path.endswith("/git/ref/heads/main"):
            edit(p)
        return httpx.Response(200, json=p)
    with pytest.raises(EvidenceReadError, match=expected):
        run(reader(reply))


def test_compare_unrelated_sha_does_not_claim_main_ancestry():
    def reply(r):
        p = payload(r)
        if "/compare/" in r.url.path:
            p["status"] = "diverged"
        return httpx.Response(200, json=p)
    assert run(reader(reply)).branch_contains_commit is False


@pytest.mark.parametrize("payload_override,expected", [
    ({"total_count": 101, "workflow_runs": []}, "GITHUB_RUNS_INCOMPLETE"),
    ({"total_count": 2, "workflow_runs": [{}]}, "GITHUB_RUNS_INCOMPLETE"),
    ({"total_count": 1, "workflow_runs": [{}]}, "GITHUB_RUN_INVALID"),
    ({"total_count": True, "workflow_runs": []}, "GITHUB_RUNS_INCOMPLETE"),
])
def test_required_ci_evidence_is_complete_or_rejected(payload_override, expected):
    def reply(r):
        p = payload(r)
        if r.url.path.endswith("/actions/runs"):
            p = payload_override
        return httpx.Response(200, json=p)
    with pytest.raises(EvidenceReadError, match=expected):
        run(reader(reply))


def core_reader(lookup):
    return CorePermissionReader(lookup=lookup, clock=lambda: NOW)


def core_run(provider, **kwargs):
    return asyncio.run(provider.read(
        access_token=kwargs.get("access_token", "x" * 50),
        authenticated_subject=kwargs.get("authenticated_subject", "user-001"),
        principal_type=kwargs.get("principal_type", "user"),
    ))


def test_core_reads_fresh_and_limits_to_explicit_deploy_permissions():
    called = []

    async def lookup(token, *, force_refresh):
        called.append((token, force_refresh))
        return {"id": "user-001", "permissions": [
            "linux_ops.deploy.view", "linux_ops.deploy.prepare", "it-portal.access",
        ], "is_superadmin": False}

    proof = core_run(core_reader(lookup))
    assert called == [("x" * 50, True)]
    assert proof.permissions == frozenset(("linux_ops.deploy.view", "linux_ops.deploy.prepare"))
    assert proof.subject == "user-001" and proof.checked_at == NOW


def test_core_superadmin_is_not_automatic_deploy_permission():
    async def lookup(*args, **kwargs):
        return {"id": "user-001", "permissions": [], "is_superadmin": True}
    assert core_run(core_reader(lookup)).permissions == frozenset()


def test_core_revocation_and_subject_drift_denied():
    async def lookup(*args, **kwargs):
        return {"id": "attacker", "permissions": ["linux_ops.deploy.prepare"]}
    with pytest.raises(EvidenceReadError, match="CORE_SUBJECT_UNVERIFIED"):
        core_run(core_reader(lookup))


@pytest.mark.parametrize("kwargs,code", [
    ({"access_token": "short"}, "CORE_TOKEN_INVALID"),
    ({"access_token": "Bearer " + "x" * 50}, "CORE_TOKEN_INVALID"),
    ({"principal_type": "service"}, "CORE_IDENTITY_INVALID"),
    ({"authenticated_subject": ""}, "CORE_IDENTITY_INVALID"),
])
def test_core_requires_identity_from_verified_user_context(kwargs, code):
    async def never(*a, **kw):
        raise AssertionError("should not call Core")
    with pytest.raises(EvidenceReadError, match=code):
        core_run(core_reader(never), **kwargs)


def test_core_unavailable_and_bad_payload_are_safe():
    async def unavailable(*a, **kw):
        raise RuntimeError("raw secret jwt=my-sensitive-token")
    with pytest.raises(EvidenceReadError) as err:
        core_run(core_reader(unavailable))
    assert err.value.code == "CORE_UNAVAILABLE" and "my-sensitive-token" not in str(err.value)

    async def bad(*a, **kw):
        return {"id": "user-001", "permissions": "linux_ops.deploy.prepare"}
    with pytest.raises(EvidenceReadError, match="CORE_PERMISSIONS_INVALID"):
        core_run(core_reader(bad))
