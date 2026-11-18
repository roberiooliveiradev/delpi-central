"""ATLAS stage 71: fail-closed Git checkout reconciliation plan.

Consumes a bounded, sanitized operator dossier; never invokes Git or writes
working trees. No fetch, pull, stash, reset, clean, checkout, chmod or deploy.
Reported upstream ancestry is an untrusted claim until separately verified.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

_SCHEMA = "atlas.hml.stage71.git-reconcile.v1"
_SHA40 = re.compile(r"[0-9a-f]{40}\Z")
_REPO = "/home/operador/projetos/delpi-central"
_ALLOWED_CHANGES = {
    "infra/scripts/up-hml-sequential.sh": "mode_100644_to_100755",
    "shared/delpi_auth.egg-info/SOURCES.txt": "one_generated_source_entry",
}
_KEYS = frozenset({
    "schema", "host", "repo_path", "branch", "local_head", "local_origin_main",
    "remote_main", "ancestry_checked_claimed", "remote_touches_dirty_claimed",
    "dirty_changes", "index_clean_claimed", "untracked_paths_present_claimed",
    "merge_or_rebase_in_progress_claimed",
})
_BLOCKS = (
    "GIT_OBSERVATIONS_NOT_INDEPENDENT",
    "MANUAL_RECONCILIATION_REQUIRED",
    "USER_CHANGES_MUST_BE_PRESERVED",
    "PULL_AND_DEPLOY_NOT_AUTHORIZED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class Stage71GitReconcileError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class Stage71GitReconcileReview:
    findings: tuple[str, ...]
    status: str = "blocked"
    pull_allowed: bool = False
    stash_allowed: bool = False
    reset_allowed: bool = False
    clean_allowed: bool = False
    deploy_allowed: bool = False
    manual_review_required: bool = True
    host_attested: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _reject_duplicate(pairs: list[tuple[str, object]]) -> dict[str, object]:
    seen: dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            raise Stage71GitReconcileError("STAGE71_GIT_DUPLICATE")
        seen[key] = value
    return seen


def _invalid_constant(_: str) -> object:
    raise Stage71GitReconcileError("STAGE71_GIT_INVALID_JSON")


def review_stage71_git_dossier(raw: bytes) -> Stage71GitReconcileReview:
    if type(raw) is not bytes or not 1 <= len(raw) <= 8192 or b"\x00" in raw:
        raise Stage71GitReconcileError("STAGE71_GIT_INPUT_DENIED")
    if any(token in raw.lower() for token in (
        b"password=", b"private key", b"secret=", b"authorization:",
        b"bearer ", b"api_key", b"token=",
    )):
        raise Stage71GitReconcileError("STAGE71_GIT_SECRET_DENIED")
    try:
        doc = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate,
            parse_constant=_invalid_constant,
        )
    except Stage71GitReconcileError:
        raise
    except (UnicodeError, ValueError, TypeError, RecursionError):
        raise Stage71GitReconcileError("STAGE71_GIT_INVALID_JSON") from None
    if type(doc) is not dict or set(doc) != _KEYS:
        raise Stage71GitReconcileError("STAGE71_GIT_SCHEMA_DENIED")
    if not (
        doc["schema"] == _SCHEMA and doc["host"] == "srv-api"
        and doc["repo_path"] == _REPO and doc["branch"] == "main"
        and all(type(doc[key]) is str and _SHA40.fullmatch(doc[key])
                for key in ("local_head", "local_origin_main", "remote_main"))
        and all(type(doc[key]) is bool for key in (
            "ancestry_checked_claimed", "remote_touches_dirty_claimed",
            "index_clean_claimed", "untracked_paths_present_claimed",
            "merge_or_rebase_in_progress_claimed",
        ))
    ):
        raise Stage71GitReconcileError("STAGE71_GIT_SCOPE_DENIED")
    dirty = doc["dirty_changes"]
    if type(dirty) is not list or len(dirty) > 32:
        raise Stage71GitReconcileError("STAGE71_GIT_DIRTY_DENIED")
    known: dict[str, str] = {}
    unknown_change = False
    for item in dirty:
        if type(item) is not dict or set(item) != {"path", "kind"}:
            raise Stage71GitReconcileError("STAGE71_GIT_DIRTY_DENIED")
        path, kind = item["path"], item["kind"]
        if type(path) is not str or type(kind) is not str:
            raise Stage71GitReconcileError("STAGE71_GIT_DIRTY_DENIED")
        if path in known:
            raise Stage71GitReconcileError("STAGE71_GIT_DUPLICATE_CHANGE")
        if path not in _ALLOWED_CHANGES or _ALLOWED_CHANGES[path] != kind:
            unknown_change = True
        known[path] = kind

    findings = ["OBSERVATION_DOSSIER_UNTRUSTED"]
    if doc["local_head"] != doc["local_origin_main"]:
        findings.append("LOCAL_TRACKING_DIVERGED")
    if doc["remote_main"] != doc["local_head"]:
        findings.append("REMOTE_AHEAD_OR_DIVERGED_REQUIRES_FRESH_ANCHOR")
    if not doc["ancestry_checked_claimed"]:
        findings.append("ANCESTRY_NOT_CHECKED")
    if doc["remote_touches_dirty_claimed"]:
        findings.append("REMOTE_CONFLICTS_LOCAL_DIRTY")
    if unknown_change:
        findings.append("UNEXPECTED_LOCAL_MODIFICATION")
    if known:
        findings.append("LOCAL_WORKTREE_DIRTY_PRESERVE")
    if not doc["index_clean_claimed"]:
        findings.append("INDEX_NOT_CLEAN")
    if doc["untracked_paths_present_claimed"]:
        findings.append("UNTRACKED_PATHS_UNREVIEWED")
    if doc["merge_or_rebase_in_progress_claimed"]:
        findings.append("ONGOING_GIT_OPERATION")
    if not known and not unknown_change:
        findings.append("NO_LOCAL_CHANGES_CLAIMED_STILL_NEEDS_VERIFICATION")
    return Stage71GitReconcileReview(findings=tuple(findings))
