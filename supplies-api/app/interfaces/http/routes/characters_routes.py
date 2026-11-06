"""Distribuição pública do avatar oficial do especialista local (SURI).

Serve apenas o arquivo aprovado declarado na ficha canônica do personagem
(``avatar_status == "OFFICIAL_AVATAR_APPROVED"`` e ``filename`` idêntico ao
basename de ``avatar_reference``). Sem resolução de caminho arbitrária e sem
fallback para imagem genérica — mesmo contrato do TÉO (AVATAR-INLINE-MCP-V1).
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from flask import Blueprint, jsonify, send_file

from app.persona.suri_profile import get_suri_profile

characters_bp = Blueprint("characters", __name__)

_API_ROOT = Path(__file__).resolve().parents[4]
_MIME_BY_SUFFIX = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
_CACHE_CONTROL = "public, max-age=300"


def _approved_avatar_path() -> Path | None:
    profile = get_suri_profile()
    appearance = profile.appearance
    reference = (appearance.avatar_reference or "").strip()
    if appearance.avatar_status != "OFFICIAL_AVATAR_APPROVED" or not reference:
        return None
    path = (_API_ROOT / reference).resolve()
    if not path.is_file() or not path.is_relative_to(_API_ROOT):
        return None
    return path


@characters_bp.get("/public/characters/<character_id>/avatar/<filename>")
def get_public_character_avatar(character_id: str, filename: str):
    profile = get_suri_profile()
    path = _approved_avatar_path()
    if (
        character_id != profile.identity.character_id
        or path is None
        or filename != PurePosixPath(profile.appearance.avatar_reference).name
    ):
        return jsonify({"detail": "Avatar do personagem não encontrado."}), 404
    response = send_file(
        path,
        mimetype=_MIME_BY_SUFFIX.get(
            path.suffix.lower(), "application/octet-stream"
        ),
    )
    response.headers["Cache-Control"] = _CACHE_CONTROL
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
