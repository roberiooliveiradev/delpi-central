"""HELPDESK-IDENTITY-001B — GLPI user profile parity with the canonical identity.

Direction: Minha DELPI identity (Keycloak claims, validated JWT)
           → Helpdesk/GLPI projection (firstname / realname).

Never the reverse; never trusts request bodies; never blanks provider fields
when the canonical source has no value. Every outcome is a distinct status —
authentication success is never proof that sync succeeded.

Write semantics (001B): runtime evidence proved the per-user OAuth token
(profile "Colaborador - Chamados", right `user`=READ) cannot PATCH
Administration/User — `GLPI_SELF_PROFILE_WRITE_NOT_AUTHORIZED`. The reconcile
therefore detects drift and reports ``deferred_write_authority`` instead of
firing a permanently-denied PATCH. Continuous write-parity for existing users
requires a separate provider authority — HELPDESK-IDENTITY-002 (ADR pending
owner decision). New users are fixed upstream by the Keycloak SAML mappers
(JIT_CREATE_PARITY).
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time

from helpdesk_app.application.oauth_service import OAuthService
from helpdesk_app.application.ports import GlpiGateway
from helpdesk_app.domain.errors import (
    GlpiForbidden,
    GlpiNotFound,
    GlpiUnavailable,
    LinkRequired,
)
from helpdesk_app.domain.models import Actor

logger = logging.getLogger("helpdesk.profile_sync")

SYNCED = "synced"
NOOP = "noop"
DEFERRED_WRITE_AUTHORITY = "deferred_write_authority"
SKIPPED_NO_CANONICAL_NAME = "skipped_no_canonical_name"
SKIPPED_NOT_LINKED = "skipped_not_linked"
SKIPPED_NO_GLPI_USER = "skipped_no_glpi_user"
FAILED_READ = "failed_read"
FAILED_FORBIDDEN = "failed_forbidden"
FAILED_UNAVAILABLE = "failed_unavailable"
FAILED_VERIFICATION = "failed_verification"
FAILED = "failed"

# In-process dedupe: the reconcile runs on every authenticated helpdesk access,
# so a settled outcome is reused within the TTL. Failures expire fast so the
# next access self-heals without hammering a rejecting provider.
_MEMO_OK_TTL_SECONDS = 3600.0
_MEMO_FAIL_TTL_SECONDS = 60.0
# Settled detections are held for the long window — skipped/failed states use
# the short TTL so the next access self-heals once linking/JIT completes.
_TERMINAL_OK = {SYNCED, NOOP, DEFERRED_WRITE_AUTHORITY}


def _clean(value: str) -> str:
    return " ".join(str(value or "").split())


class ProfileSyncService:
    """Idempotent drift detection: canonical first/last name vs GLPI profile.

    Reads the caller's own GLPI user (``user_id`` resolved from the OAuth
    session) and compares ``firstname``/``realname`` to the validated identity
    claims. On divergence it reports ``deferred_write_authority`` — the
    user-scoped OAuth authority provably cannot write User names (GLPI right
    `user`=READ), so no PATCH is attempted. Write-parity is deferred to the
    dedicated authority decided in HELPDESK-IDENTITY-002.
    """

    def __init__(self, glpi: GlpiGateway, oauth: OAuthService, *, now=None):
        self._glpi = glpi
        self._oauth = oauth
        self._now = now or time.monotonic
        self._memo: dict[str, tuple[tuple[str, str], str, float]] = {}
        self._lock = threading.Lock()

    def ensure_profile(self, actor: Actor) -> str:
        subject = (actor.subject or "").strip()
        if not subject:
            return FAILED

        first = _clean(actor.first_name)
        last = _clean(actor.last_name)
        if not first and not last:
            # No authoritative split — never invent one, never blank GLPI fields.
            return SKIPPED_NO_CANONICAL_NAME

        try:
            token = self._oauth.access_token_for(subject)
        except LinkRequired:
            # In-memory session lookup, no provider I/O — always re-checked,
            # never memoized, so a just-completed OAuth link reconciles at once.
            return SKIPPED_NOT_LINKED

        # Memo key = hashed token: a re-link/refresh yields a new key, so a
        # stale outcome can never leak into a different GLPI session.
        memo_key = hashlib.sha256(token.encode()).hexdigest()
        cached = self._cached(memo_key, first, last)
        if cached is not None:
            return cached

        status = self._reconcile(actor, token, first, last, subject)
        with self._lock:
            self._memo[memo_key] = ((first, last), status, self._now())
        return status

    def _cached(self, memo_key: str, first: str, last: str) -> str | None:
        with self._lock:
            entry = self._memo.get(memo_key)
        if entry is None:
            return None
        (memo_first, memo_last), status, at = entry
        if (memo_first, memo_last) != (first, last):
            return None  # canonical name changed — reconcile again
        ttl = _MEMO_OK_TTL_SECONDS if status in _TERMINAL_OK else _MEMO_FAIL_TTL_SECONDS
        if self._now() - at > ttl:
            return None
        return status

    def _reconcile(self, actor: Actor, token: str, first: str, last: str, subject: str) -> str:
        try:
            user_id = self._glpi.session_user_id(token)
        except GlpiUnavailable:
            logger.warning("helpdesk_profile_sync outcome=%s subject=%s stage=session", FAILED_UNAVAILABLE, subject)
            return FAILED_UNAVAILABLE
        except Exception:
            logger.exception("helpdesk_profile_sync outcome=%s subject=%s stage=session", FAILED, subject)
            return FAILED
        if not user_id:
            return SKIPPED_NO_GLPI_USER

        try:
            current = self._glpi.get_user(token, user_id)
        except GlpiForbidden:
            logger.warning("helpdesk_profile_sync outcome=%s subject=%s user_id=%s stage=read", FAILED_FORBIDDEN, subject, user_id)
            return FAILED_FORBIDDEN
        except GlpiNotFound:
            current = None
        except GlpiUnavailable:
            logger.warning("helpdesk_profile_sync outcome=%s subject=%s user_id=%s stage=read", FAILED_UNAVAILABLE, subject, user_id)
            return FAILED_UNAVAILABLE
        except Exception:
            logger.exception("helpdesk_profile_sync outcome=%s subject=%s user_id=%s stage=read", FAILED, subject, user_id)
            return FAILED
        if current is None:
            return SKIPPED_NO_GLPI_USER

        diff = self._diff(current, first, last)
        if not diff:
            return NOOP

        # Drift detected. The user-scoped OAuth token provably lacks `user`
        # UPDATE (PROVEN: profile "Colaborador - Chamados", rights=READ) —
        # write is intentionally deferred to the IDENTITY-002 authority.
        logger.warning(
            "helpdesk_profile_sync outcome=%s subject=%s user_id=%s stage=diff fields=%s",
            DEFERRED_WRITE_AUTHORITY,
            subject,
            user_id,
            sorted(diff),
        )
        return DEFERRED_WRITE_AUTHORITY

    @staticmethod
    def _diff(profile, first: str, last: str) -> dict:
        """Fields whose canonical value differs — empty canonical never counts
        as drift (an absent claim must never be projected as a blank name)."""
        diff: dict = {}
        if first and _clean(profile.firstname) != first:
            diff["firstname"] = first
        if last and _clean(profile.realname) != last:
            diff["realname"] = last
        return diff
