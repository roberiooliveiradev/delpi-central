from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

from tv_app.core.security import TV_ADMIN, can
from tv_app.infrastructure.persistence.repositories.playlist_repository import PlaylistRepository

PlaylistAccessLevel = Literal["none", "viewer", "editor", "owner"]


@dataclass(frozen=True)
class PlaylistAccess:
    level: PlaylistAccessLevel
    playlist: dict[str, Any] | None = None

    @property
    def can_read(self) -> bool:
        return self.level in {"viewer", "editor", "owner"}

    @property
    def can_edit(self) -> bool:
        return self.level in {"editor", "owner"}

    @property
    def can_manage(self) -> bool:
        """Dono: shares, invite, delete, regenerar token público."""
        return self.level == "owner"


class PlaylistAccessService:
    """Autorização por recurso: owner_user_id ou share.target_user_id."""

    def __init__(self, repo: PlaylistRepository | None = None) -> None:
        self._repo = repo or PlaylistRepository()

    @staticmethod
    def actor_id(user: Any | None) -> str | None:
        if user is None:
            return None
        sub = getattr(user, "sub", None) or getattr(user, "preferred_username", None)
        if sub is None:
            return None
        value = str(sub).strip()
        return value or None

    def resolve(self, playlist_id: UUID, user: Any | None) -> PlaylistAccess:
        playlist = self._repo.get_by_id(playlist_id)
        if not playlist:
            return PlaylistAccess(level="none")

        actor = self.actor_id(user)
        if not actor:
            return PlaylistAccess(level="none", playlist=playlist)

        # Admin do módulo vê/edita tudo (suporte); ownership continua no registro.
        if can(user, TV_ADMIN):
            return PlaylistAccess(level="owner", playlist=playlist)

        owner = str(playlist.get("ownerUserId") or playlist.get("createdBy") or "").strip()
        if owner and owner == actor:
            return PlaylistAccess(level="owner", playlist=playlist)

        share_role = self._repo.get_share_role(playlist_id, actor)
        if share_role == "editor":
            return PlaylistAccess(level="editor", playlist=playlist)
        if share_role == "viewer":
            return PlaylistAccess(level="viewer", playlist=playlist)

        # Legado sem dono: só admin (já tratado) — usuários comuns não veem.
        return PlaylistAccess(level="none", playlist=playlist)
