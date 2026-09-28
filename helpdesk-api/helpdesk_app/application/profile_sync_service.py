"""HELPDESK-IDENTITY-001 — GLPI user profile parity with the canonical identity.

Direction: Minha DELPI identity (Keycloak claims, validated JWT)
           → Helpdesk/GLPI projection (firstname / realname).

Never the reverse; never trusts request bodies; never blanks provider fields
when the canonical source has no value. Every outcome is a distinct status —
authentication success is never proof that sync succeeded.
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
    GlpiUnauthorized,
    GlpiUnavailable,
    GlpiValidation,
    LinkRequired,
)
from helpdesk_app.domain.models import Actor

logger = logging.getLogger("helpdesk.profile_sync")

SYNCED = "synced"
NOOP = "noop"
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
# Only settled parity is held for the long window — skipped/failed states use
# the short TTL so the next access self-heals once linking/JIT completes.
_TERMINAL_OK = {SYNCED, NOOP}


def _clean(value: str) -> str:
    return " ".join(str(value or "").split())


class ProfileSyncService:
    """Idempotent reconcile: canonical first/last name → GLPI firstname/realname.

    Write is self-scoped: the only target is the GLPI ``user_id`` resolved from
    the caller's own OAuth session, and the payload comes exclusively from the
    validated identity claims. The provider may still deny the write (profile
    without the ``user`` UPDATE right) — that surfaces as ``failed_forbidden``,
    never as success.
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
        # stale "synced" can never leak into a different GLPI session.
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

        try:
            self._glpi.update_user_profile(token, user_id, **diff)
        except GlpiForbidden:
            logger.warning("helpdesk_profile_sync outcome=%s subject=%s user_id=%s stage=write fields=%s", FAILED_FORBIDDEN, subject, user_id, sorted(diff))
            return FAILED_FORBIDDEN
        except (GlpiNotFound, GlpiValidation, GlpiUnauthorized):
            logger.warning("helpdesk_profile_sync outcome=%s subject=%s user_id=%s stage=write fields=%s", FAILED, subject, user_id, sorted(diff))
            return FAILED
        except GlpiUnavailable:
            logger.warning("helpdesk_profile_sync outcome=%s subject=%s user_id=%s stage=write", FAILED_UNAVAILABLE, subject, user_id)
            return FAILED_UNAVAILABLE
        except Exception:
            logger.exception("helpdesk_profile_sync outcome=%s subject=%s user_id=%s stage=write", FAILED, subject, user_id)
            return FAILED

        # Postcondition: HTTP 2xx is not proof — reread the provider state.
        try:
            refreshed = self._glpi.get_user(token, user_id)
        except Exception:
            logger.exception("helpdesk_profile_sync outcome=%s subject=%s user_id=%s stage=verify", FAILED, subject, user_id)
            return FAILED
        if refreshed is None or self._diff(refreshed, first, last):
            logger.warning("helpdesk_profile_sync outcome=%s subject=%s user_id=%s stage=verify", FAILED_VERIFICATION, subject, user_id)
            return FAILED_VERIFICATION

        logger.info("helpdesk_profile_sync outcome=%s subject=%s user_id=%s fields=%s", SYNCED, subject, user_id, sorted(diff))
        return SYNCED

    @staticmethod
    def _diff(profile, first: str, last: str) -> dict:
        """Only non-empty canonical values are written — empty never erases."""
        diff: dict = {}
        if first and _clean(profile.firstname) != first:
            diff["firstname"] = first
        if last and _clean(profile.realname) != last:
            diff["realname"] = last
        return diff
