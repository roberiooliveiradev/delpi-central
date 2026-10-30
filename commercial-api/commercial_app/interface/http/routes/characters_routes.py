"""Distribuição pública do avatar oficial do especialista local (CAIO).

DELPI-CHARACTER-AVATARS-001-R01 pattern: publicação pública aprovada
pelo PO. Serve apenas o arquivo aprovado declarado na ficha canônica
do personagem (``avatar_status == "OFFICIAL_AVATAR_APPROVED"`` e
``filename`` idêntico ao basename de ``avatar_reference``). O path
entra na allowlist pública do ``jwt_middleware`` por comparação exata.
Sem resolução de caminho arbitrária e sem fallback para imagem
genérica — enquanto o asset original estiver PENDING_ASSET, a rota
responde 404 honestamente.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from fastapi import APIRouter
from fastapi.responses import FileResponse

from commercial_app.core.responses import fail
from commercial_app.persona.caio_profile import get_caio_profile

router = APIRouter(prefix="/public/characters", tags=["Characters"])

# R01: distribuição pública aprovada pelo PO — gate aberto. Os controles de
# aprovação da ficha e de correspondência exata permanecem ativos abaixo.
_PUBLIC_DISTRIBUTION_ENABLED = True

_API_ROOT = Path(__file__).resolve().parents[4]
_MIME_BY_SUFFIX = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
_CACHE_CONTROL = "public, max-age=300"


def _approved_avatar_path() -> Path | None:
    profile = get_caio_profile()
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
    profile = get_caio_profile()
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
