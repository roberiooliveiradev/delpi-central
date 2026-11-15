"""P2.2b backend-only, read-only GitHub and Core proof readers.

No MCP tools, executor, shell, Docker, SQL or deployment capabilities here.
Callers MUST derive the OAuth subject/token from verified server-side identity,
not from user/model arguments. The configured workflow policy is server-owned.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Awaitable, Callable

import httpx

from .deploy_attestation import CoreProof, GithubProof, WorkflowRunProof

_API = "https://api.github.com"
_REPO = "roberiooliveiradev/delpi-central"
_PREFIX = f"/repos/{_REPO}"
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_MAX_RESPONSE = 256_000
_ALLOWED_PERMISSIONS = frozenset(("linux_ops.deploy.view", "linux_ops.deploy.prepare"))


class EvidenceReadError(Exception):
    """Only a safe error code, never URL/body/token/upstream exception details."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _timestamp(clock: Callable[[], datetime]) -> datetime:
    value = clock()
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise EvidenceReadError("PROOF_CLOCK_INVALID")
    return value.astimezone(timezone.utc)


class GithubReleaseReader:
    """Pinned GitHub API origin/repository; no caller-selected URLs or refs."""

    def __init__(
        self, *, token: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        if token is not None and (type(token) is not str or not token.strip() or "\n" in token or "\r" in token):
            raise EvidenceReadError("GITHUB_CREDENTIAL_INVALID")
        self._token = token
        self._transport = transport
        self._clock = clock

    async def _json(self, client: httpx.AsyncClient, path: str, params: dict[str, str] | None = None) -> dict:
        # Internal fixed paths only. All variable path segments are 40-hex SHA.
        try:
            async with client.stream("GET", f"{_API}{_PREFIX}{path}", params=params) as response:
                if response.status_code != 200 or not response.headers.get("content-type", "").lower().startswith("application/json"):
                    raise EvidenceReadError("GITHUB_UNAVAILABLE")
                data = bytearray()
                async for chunk in response.aiter_bytes():
                    data.extend(chunk)
                    if len(data) > _MAX_RESPONSE:
                        raise EvidenceReadError("GITHUB_RESPONSE_TOO_LARGE")
            payload = json.loads(data)
            if type(payload) is not dict:
                raise EvidenceReadError("GITHUB_RESPONSE_INVALID")
            return payload
        except EvidenceReadError:
            raise
        except (httpx.HTTPError, json.JSONDecodeError, UnicodeError, ValueError):
            raise EvidenceReadError("GITHUB_UNAVAILABLE") from None

    async def read(self, commit_sha: str) -> GithubProof:
        if not _sha(commit_sha):
            raise EvidenceReadError("COMMIT_SHA_INVALID")
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        async with httpx.AsyncClient(
            headers=headers, timeout=5.0, trust_env=False,
            follow_redirects=False, transport=self._transport,
        ) as client:
            ref = await self._json(client, "/git/ref/heads/main")
            obj = ref.get("object")
            head_sha = obj.get("sha") if type(obj) is dict else None
            if ref.get("ref") != "refs/heads/main" or not _sha(head_sha) or obj.get("type") != "commit":
                raise EvidenceReadError("GITHUB_REF_UNVERIFIED")

            compare = await self._json(client, f"/compare/{commit_sha}...{head_sha}", {"per_page": "1"})
            base = compare.get("base_commit")
            head = compare.get("head_commit")
            ancestry = (compare.get("status") in ("ahead", "identical")
                        and type(base) is dict and base.get("sha") == commit_sha
                        and type(head) is dict and head.get("sha") == head_sha)

            actions = await self._json(client, "/actions/runs", {
                "head_sha": commit_sha, "event": "push", "per_page": "100",
            })
            runs = actions.get("workflow_runs")
            count = actions.get("total_count")
            if type(count) is not int or count < 0 or count > 100 or type(runs) is not list or len(runs) > 100:
                raise EvidenceReadError("GITHUB_RUNS_INCOMPLETE")
            if len(runs) != count:
                raise EvidenceReadError("GITHUB_RUNS_INCOMPLETE")
            mapped: list[WorkflowRunProof] = []
            for item in runs:
                if type(item) is not dict:
                    raise EvidenceReadError("GITHUB_RUN_INVALID")
                wid, rid, attempt = item.get("workflow_id"), item.get("id"), item.get("run_attempt")
                if not all(type(n) is int and n > 0 for n in (wid, rid, attempt)):
                    raise EvidenceReadError("GITHUB_RUN_INVALID")
                if not all(type(item.get(k)) is str for k in ("head_sha", "head_branch", "event", "status")):
                    raise EvidenceReadError("GITHUB_RUN_INVALID")
                if item.get("conclusion") is not None and type(item.get("conclusion")) is not str:
                    raise EvidenceReadError("GITHUB_RUN_INVALID")
                mapped.append(WorkflowRunProof(
                    workflow_id=wid, run_id=rid, attempt=attempt,
                    head_sha=item["head_sha"], head_branch=item["head_branch"],
                    event=item["event"], status=item["status"], conclusion=item.get("conclusion"),
                ))
        return GithubProof(_REPO, commit_sha, "main", bool(ancestry), tuple(mapped), _timestamp(self._clock))


class CorePermissionReader:
    """Use existing canonical Core /me force-refresh, with no stale fallback."""

    def __init__(
        self, *, lookup: Callable[..., Awaitable[dict]] | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        self._lookup = lookup
        self._clock = clock

    async def read(self, *, access_token: str, authenticated_subject: str, principal_type: str) -> CoreProof:
        # All three parameters are to come from verified backend MCP context.
        if (type(access_token) is not str or len(access_token) < 20
                or access_token.startswith("Bearer ") or any(c in access_token for c in "\n\r")):
            raise EvidenceReadError("CORE_TOKEN_INVALID")
        if type(authenticated_subject) is not str or not authenticated_subject or principal_type != "user":
            raise EvidenceReadError("CORE_IDENTITY_INVALID")
        try:
            if self._lookup is None:
                from delpi_auth.middleware.fastapi_auth import load_user_rbac
                lookup = load_user_rbac
            else:
                lookup = self._lookup
            data = await lookup(access_token, force_refresh=True)
        except Exception:
            raise EvidenceReadError("CORE_UNAVAILABLE") from None
        if type(data) is not dict or str(data.get("id") or "") != authenticated_subject:
            raise EvidenceReadError("CORE_SUBJECT_UNVERIFIED")
        permissions = data.get("permissions")
        if type(permissions) is not list or len(permissions) > 400 or any(type(p) is not str or len(p) > 128 for p in permissions):
            raise EvidenceReadError("CORE_PERMISSIONS_INVALID")
        explicit = frozenset(p for p in permissions if p in _ALLOWED_PERMISSIONS)
        # Deliberately DO NOT convert is_superadmin into an implicit grant.
        return CoreProof(authenticated_subject, "user", explicit, _timestamp(self._clock))
