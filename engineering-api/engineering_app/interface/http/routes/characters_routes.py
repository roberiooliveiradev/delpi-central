"""Distribuição do avatar oficial da especialista local (EVA).

DELPI-CHARACTER-AVATARS-001 (D05): a publicação pública da EVA permanece
``DECISION_REQUIRED`` até a ratificação do PO. A implementação owner-local
está preparada mas desabilitada — toda requisição responde 404 e o path não
entra na allowlist pública do middleware enquanto o gate estiver fechado.

Para ativar: (1) ratificação do PO, (2) ``_PUBLIC_DISTRIBUTION_ENABLED = True``,
(3) incluir o prefixo ``/public/characters/`` na allowlist pública do
``jwt_middleware``.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from fastapi import APIRouter
from fastapi.responses import FileResponse

from engineering_app.core.responses import fail
from engineering_app.persona.eva_profile import get_eva_profile

router = APIRouter(prefix="/public/characters", tags=["Characters"])

_PUBLIC_DISTRIBUTION_ENABLED = False  # D05 — PO ratification pending.

_API_ROOT = Path(__file__).resolve().parents[4]
_MIME_BY_SUFFIX = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
_CACHE_CONTROL = "public, max-age=300"


def _approved_avatar_path() -> Path | None:
    profile = get_eva_profile()
    appearance = profile.appearance
    reference = (appearance.avatar_reference or "").strip()
    if appearance.avatar_status != "OFFICIAL_AVATAR_APPROVED" or not reference:
        return None
    path = (_API_ROOT / reference).resolve()
    if not path.is_file() or not path.is_relative_to(_API_ROOT):
        return None
    return path


@router.get(
    "/{character_id}/avatar/{filename}",
    operation_id="get_public_character_avatar",
)
def get_public_character_avatar(character_id: str, filename: str):
    profile = get_eva_profile()
    path = _approved_avatar_path() if _PUBLIC_DISTRIBUTION_ENABLED else None
    if (
        character_id != profile.identity.character_id
        or path is None
        or filename != PurePosixPath(profile.appearance.avatar_reference).name
    ):
        return fail("Avatar do personagem não encontrado.", 404)
    return FileResponse(
        path,
        media_type=_MIME_BY_SUFFIX.get(path.suffix.lower(), "application/octet-stream"),
        headers={
            "Cache-Control": _CACHE_CONTROL,
            "X-Content-Type-Options": "nosniff",
        },
    )
