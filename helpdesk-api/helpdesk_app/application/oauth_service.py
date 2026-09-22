import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from helpdesk_app.application.ports import GlpiGateway, SessionStore, StateStore
from helpdesk_app.domain.errors import GlpiUnauthorized, GlpiValidation, InvalidOAuthState, LinkRequired
from helpdesk_app.domain.models import OAuthSession

STATE_TTL = timedelta(minutes=10)
ACCESS_SKEW = timedelta(seconds=30)


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


class OAuthService:
    def __init__(self, glpi: GlpiGateway, states: StateStore, sessions: SessionStore, now=None):
        self._glpi = glpi
        self._states = states
        self._sessions = sessions
        self._now = now or (lambda: datetime.now(timezone.utc))

    def start(self, subject: str) -> str:
        state = secrets.token_urlsafe(32)
        verifier, challenge = _pkce_pair()
        self._states.save(
            state=state,
            subject=subject,
            code_verifier=verifier,
            expires_at=self._now() + STATE_TTL,
        )
        return self._glpi.authorization_url(state=state, code_challenge=challenge)

    def complete(self, *, code: str, state: str) -> str:
        pending = self._states.consume(state)
        if pending is None:
            raise InvalidOAuthState("Estado OAuth inválido ou expirado.")
        tokens = self._glpi.exchange_code(code=code, code_verifier=pending.code_verifier)
        self._sessions.save(
            OAuthSession(
                subject=pending.subject,
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                access_expires_at=self._now() + timedelta(seconds=tokens.expires_in),
            )
        )
        return pending.subject

    def linked(self, subject: str) -> bool:
        return self._sessions.get(subject) is not None

    def unlink(self, subject: str) -> None:
        self._sessions.delete(subject)

    def access_token_for(self, subject: str) -> str:
        session = self._sessions.get(subject)
        if session is None:
            raise LinkRequired("É preciso autorizar o GLPI antes de abrir chamados.")
        if session.access_expires_at - ACCESS_SKEW <= self._now():
            session = self._refresh(session)
        return session.access_token

    def _refresh(self, session: OAuthSession) -> OAuthSession:
        try:
            tokens = self._glpi.refresh(session.refresh_token)
        except (GlpiUnauthorized, GlpiValidation) as exc:
            self._sessions.delete(session.subject)
            raise LinkRequired("A sessão do GLPI expirou. Autorize de novo.") from exc
        updated = OAuthSession(
            subject=session.subject,
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token or session.refresh_token,
            access_expires_at=self._now() + timedelta(seconds=tokens.expires_in),
        )
        self._sessions.save(updated)
        return updated
