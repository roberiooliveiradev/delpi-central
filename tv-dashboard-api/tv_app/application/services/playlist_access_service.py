from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping
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
        """Id canônico do JWT/RBAC (`user.id` no delpi_auth). Não usar e-mail."""
        if user is None:
            return None
        for attr in ("id", "sub", "preferred_username"):
            raw = user.get(attr) if isinstance(user, Mapping) else getattr(user, attr, None)
            if raw is None:
                continue
            value = str(raw).strip()
            if value:
                return value
        return None

    def resolve(self, playlist_id: UUID, user: Any | None) -> PlaylistAccess:
        playlist = self._repo.get_by_id(playlist_id)
        if not playlist:
            return PlaylistAccess(level="none")

        # Admin do módulo / superadmin: acesso total; órfã recebe dono na abertura (suporte).
        if can(user, TV_ADMIN):
            actor = self.actor_id(user)
            owner = str(playlist.get("ownerUserId") or playlist.get("createdBy") or "").strip()
            if not owner and actor:
                claimed = self._repo.try_claim_owner(playlist_id, actor)
                if claimed:
                    return PlaylistAccess(level="owner", playlist=claimed)
            return PlaylistAccess(level="owner", playlist=playlist)

        actor = self.actor_id(user)
        if not actor:
            return PlaylistAccess(level="none", playlist=playlist)

        owner = str(playlist.get("ownerUserId") or playlist.get("createdBy") or "").strip()
        if owner and owner == actor:
            return PlaylistAccess(level="owner", playlist=playlist)

        share_role = self._repo.get_share_role(playlist_id, actor)
        if share_role == "editor":
            return PlaylistAccess(level="editor", playlist=playlist)
        if share_role == "viewer":
            return PlaylistAccess(level="viewer", playlist=playlist)

        # Órfã: usuário comum não vê — admin trata acima.
        return PlaylistAccess(level="none", playlist=playlist)
