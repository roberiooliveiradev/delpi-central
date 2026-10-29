"""Distribuição pública do avatar oficial da especialista local (VISTA).

Serve apenas o arquivo aprovado declarado na ficha canônica do personagem
(``avatar_status == "OFFICIAL_AVATAR_APPROVED"`` e ``filename`` idêntico ao
basename de ``avatar_reference``). Sem resolução de caminho arbitrária e sem
fallback para imagem genérica.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from fastapi import APIRouter

from tv_app.core.responses import fail
from tv_app.interface.http.media_file_response import build_media_file_response
from tv_app.persona.vista_profile import get_vista_profile

router = APIRouter(prefix="/public/characters", tags=["Characters"])

_API_ROOT = Path(__file__).resolve().parents[4]
_MIME_BY_SUFFIX = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
_CACHE_CONTROL = "public, max-age=300"


def _approved_avatar_path() -> Path | None:
    profile = get_vista_profile()
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
    profile = get_vista_profile()
    path = _approved_avatar_path()
    if (
        character_id != profile.identity.character_id
        or path is None
        or filename != PurePosixPath(profile.appearance.avatar_reference).name
    ):
        return fail("Avatar do personagem não encontrado.", 404)
    return build_media_file_response(
        path=path,
        mime_type=_MIME_BY_SUFFIX.get(path.suffix.lower(), "application/octet-stream"),
        cache_control=_CACHE_CONTROL,
    )
