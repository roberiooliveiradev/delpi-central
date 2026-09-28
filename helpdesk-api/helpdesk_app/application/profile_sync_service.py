"""HELPDESK-IDENTITY-002A — GLPI user profile parity with the canonical identity.

Direction: Keycloak (canonical identity owner)
           → session projection (validated JWT given_name/family_name)
           → Helpdesk/GLPI projection (firstname / realname).

Never the reverse; never trusts request bodies; never blanks provider fields
when the canonical source has no value. Every outcome is a distinct status —
authentication success is never proof that sync succeeded.

Write semantics: the per-user OAuth token provably cannot write
Administration/User names (GLPI_SELF_PROFILE_WRITE_NOT_AUTHORIZED — profile
"Colaborador - Chamados", right `user`=READ). With no technical writer
configured, drift is reported as ``deferred_write_authority`` and ZERO write
is attempted (001B). When a ``ProfileSyncWriterPort`` is wired (dedicated
backend principal — feature-flagged), drift triggers a names-only technical
write followed by an authoritative reread; ``synced`` is reported only when
the reread proves parity.

Cadence semantics: one bounded reconciliation per Keycloak session — the
memo key is ``hash(subject | sid)``, never token material (access tokens
rotate inside a session). A canonical-profile fingerprint is stored instead
of raw names: same sub+sid+fingerprint → memoized; changed fingerprint or
new sid → fresh reconcile. Memo is process-local; the deployment is a
single uvicorn worker, so this is bounded/idempotent per runtime instance —
not a distributed exactly-once claim.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time

from helpdesk_app.application.oauth_service import OAuthService
from helpdesk_app.application.ports import GlpiGateway, ProfileSyncWriterPort
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
FAILED_WRITE = "failed_write"
FAILED_FORBIDDEN = "failed_forbidden"
FAILED_UNAVAILABLE = "failed_unavailable"
FAILED_VERIFICATION = "failed_verification"
FAILED = "failed"

# Terminal outcomes outlive a Keycloak session (ssoSessionMaxLifespan 10h —
# cap at 12h for memory hygiene). Failures expire fast so the next access
# self-heals without hammering a rejecting provider.
_MEMO_OK_TTL_SECONDS = 12 * 3600.0
_MEMO_FAIL_TTL_SECONDS = 60.0
_TERMINAL_OK = {SYNCED, NOOP, DEFERRED_WRITE_AUTHORITY}


def _clean(value: str) -> str:
    return " ".join(str(value or "").split())


def _fingerprint(first: str, last: str) -> str:
    """Non-reversible canonical-profile fingerprint — memo never stores names."""
    return hashlib.sha256(f"{first}\x1f{last}".encode()).hexdigest()


class ProfileSyncService:
    """Idempotent profile parity: canonical first/last name vs GLPI profile.

    Reads the caller's own GLPI user (``user_id`` resolved from the OAuth
    session) and compares ``firstname``/``realname`` to the validated identity
    claims. On divergence:

    * no writer wired → ``deferred_write_authority`` (zero PATCH);
    * writer wired → technical names-only write + authoritative reread.

    The write target is always the session-resolved ``user_id`` — never a
    request-supplied id — and failure never blocks the Helpdesk request.
    """

    def __init__(
        self,
        glpi: GlpiGateway,
        oauth: OAuthService,
        *,
        writer: ProfileSyncWriterPort | None = None,
        now=None,
    ):
        self._glpi = glpi
        self._oauth = oauth
        self._writer = writer
        self._now = now or time.monotonic
        # key → (canonical fingerprint, status, monotonic ts)
        self._memo: dict[str, tuple[str, str, float]] = {}
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

        # Semantic session key: subject + Keycloak sid. No token hash —
        # access tokens rotate inside a session and must not split it.
        memo_key = hashlib.sha256(
            f"{subject}\x1f{actor.session_id or ''}".encode()
        ).hexdigest()
        fingerprint = _fingerprint(first, last)
        cached = self._cached(memo_key, fingerprint)
        if cached is not None:
            return cached

        status = self._reconcile(actor, token, first, last, subject)
        with self._lock:
            self._memo[memo_key] = (fingerprint, status, self._now())
        return status

    def _cached(self, memo_key: str, fingerprint: str) -> str | None:
        with self._lock:
            entry = self._memo.get(memo_key)
        if entry is None:
            return None
        memo_fingerprint, status, at = entry
        if memo_fingerprint != fingerprint:
            return None  # canonical profile changed mid-session — reconcile again
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

        # Drift detected. Without a technical writer the user-scoped OAuth
        # token provably lacks `user` UPDATE — defer, zero PATCH (001B).
        if self._writer is None:
            logger.warning(
                "helpdesk_profile_sync outcome=%s subject=%s user_id=%s stage=diff fields=%s",
                DEFERRED_WRITE_AUTHORITY,
                subject,
                user_id,
                sorted(diff),
            )
            return DEFERRED_WRITE_AUTHORITY

        return self._write_and_verify(subject, user_id, diff, token)

    def _write_and_verify(self, subject: str, user_id: int, diff: dict, token: str) -> str:
        """Technical write via the dedicated principal + authoritative reread.

        Only the divergent name fields are sent — nothing else reaches the
        provider. ``synced`` requires the reread to prove parity.
        """
        fields = sorted(diff)
        try:
            self._writer.update_profile_names(
                int(user_id),
                firstname=diff.get("firstname"),
                realname=diff.get("realname"),
            )
        except GlpiForbidden:
            logger.warning(
                "helpdesk_profile_sync outcome=%s actor=system/profile-sync subject=%s user_id=%s stage=write fields=%s",
                FAILED_FORBIDDEN, subject, user_id, fields,
            )
            return FAILED_FORBIDDEN
        except GlpiUnavailable:
            logger.warning(
                "helpdesk_profile_sync outcome=%s actor=system/profile-sync subject=%s user_id=%s stage=write fields=%s",
                FAILED_UNAVAILABLE, subject, user_id, fields,
            )
            return FAILED_UNAVAILABLE
        except Exception:
            logger.exception(
                "helpdesk_profile_sync outcome=%s actor=system/profile-sync subject=%s user_id=%s stage=write fields=%s",
                FAILED_WRITE, subject, user_id, fields,
            )
            return FAILED_WRITE

        logger.info(
            "helpdesk_profile_sync actor=system/profile-sync event=technical_write subject=%s user_id=%s fields=%s",
            subject, user_id, fields,
        )

        # Authoritative postcondition: reread via the user's own session —
        # the technical writer must not become the general read authority.
        try:
            after = self._glpi.get_user(token, user_id)
        except GlpiForbidden:
            logger.warning(
                "helpdesk_profile_sync outcome=%s subject=%s user_id=%s stage=verify",
                FAILED_FORBIDDEN, subject, user_id,
            )
            return FAILED_FORBIDDEN
        except GlpiUnavailable:
            logger.warning(
                "helpdesk_profile_sync outcome=%s subject=%s user_id=%s stage=verify",
                FAILED_UNAVAILABLE, subject, user_id,
            )
            return FAILED_UNAVAILABLE
        except Exception:
            logger.exception(
                "helpdesk_profile_sync outcome=%s subject=%s user_id=%s stage=verify",
                FAILED, subject, user_id,
            )
            return FAILED

        if after is None or self._diff(after, diff.get("firstname", ""), diff.get("realname", "")):
            logger.warning(
                "helpdesk_profile_sync outcome=%s subject=%s user_id=%s stage=verify fields=%s",
                FAILED_VERIFICATION, subject, user_id, fields,
            )
            return FAILED_VERIFICATION

        logger.info(
            "helpdesk_profile_sync outcome=%s subject=%s user_id=%s fields=%s",
            SYNCED, subject, user_id, fields,
        )
        return SYNCED

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
