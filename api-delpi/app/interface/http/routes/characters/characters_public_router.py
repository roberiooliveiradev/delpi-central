"""Distribuição pública do avatar oficial do especialista local (DAVI).

A rota serve apenas o arquivo aprovado declarado na ficha canônica do
personagem (``appearance.avatar_status == "OFFICIAL_AVATAR_APPROVED"`` e
``filename`` idêntico ao basename de ``avatar_reference``). Não há resolução
de caminho arbitrária nem fallback para imagem genérica.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.core.responses import not_found_response
from app.persona.davi_profile import get_davi_profile

router = APIRouter(prefix="/public/characters", tags=["Characters"])

_API_ROOT = Path(__file__).resolve().parents[5]
_MIME_BY_SUFFIX = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
_CACHE_CONTROL = "public, max-age=300"


def _approved_avatar_path() -> Path | None:
    profile = get_davi_profile()
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
    profile = get_davi_profile()
    path = _approved_avatar_path()
    if (
        character_id != profile.identity.character_id
        or path is None
        or filename != PurePosixPath(profile.appearance.avatar_reference).name
    ):
        return not_found_response("Avatar do personagem não encontrado")
    return FileResponse(
        path,
        media_type=_MIME_BY_SUFFIX.get(path.suffix.lower(), "application/octet-stream"),
        headers={
            "Cache-Control": _CACHE_CONTROL,
            "X-Content-Type-Options": "nosniff",
        },
    )
