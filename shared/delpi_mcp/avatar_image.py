"""Approved character avatar → MCP ``ImageContent`` delivery mechanics.

AVATAR-INLINE-MCP-V1 — transport-neutral helper owned by the MCP
interface layer (``delpi_mcp``). Given a canonical ``CharacterProfile``
and the owning service's filesystem root, it resolves the *approved*
avatar reference, validates the resolved path, computes integrity
metadata and builds the canonical ``ImageContent`` block.

Ownership contract:

- this module owns the *mechanics* (path resolution, allowlist checks,
  MIME map, sha256, size cap, base64 encoding);
- each MCP owner keeps the *response semantics* (auth gate, error
  shape, message text) — see ``build_avatar_delivery``;
- it never imports MCP owner internals, never resolves user-supplied
  paths/URLs and never fabricates an asset — ``data``/``image`` are
  ``None`` whenever the canonical avatar is not
  ``OFFICIAL_AVATAR_APPROVED`` or the file is missing/outside root.
"""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

AVATAR_INLINE_MAX_BYTES = 8 * 1024 * 1024
AVATAR_MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


@dataclass
class AvatarDelivery:
    """Result parts of an approved-avatar inline delivery.

    ``data`` carries the structured metadata for the tool result and is
    ``None`` when the canonical avatar is not approved or the asset is
    missing/outside the service root (safe fail — publish nothing for
    unapproved or unresolvable references). ``image`` is the canonical
    ``ImageContent`` block, ``None`` when delivery stays metadata-only.
    """

    data: dict[str, Any] | None
    image: Any | None  # mcp.types.ImageContent — lazy-imported by callers
    display_name: str | None
    too_large: bool = False


def approved_avatar_path(profile: Any, service_root: Path) -> Path | None:
    """Resolve the canonical approved avatar path or ``None``.

    The reference comes exclusively from the ficha's
    ``avatar_reference`` when ``avatar_status`` is
    ``OFFICIAL_AVATAR_APPROVED`` — never from user input. The resolved
    path must exist and stay inside ``service_root``.
    """
    appearance = profile.appearance
    reference = (appearance.avatar_reference or "").strip()
    if appearance.avatar_status != "OFFICIAL_AVATAR_APPROVED" or not reference:
        return None
    root = Path(service_root).resolve()
    path = (root / reference).resolve()
    if not path.is_file() or not path.is_relative_to(root):
        return None
    return path


def avatar_mime(path: Path) -> str:
    return AVATAR_MIME_BY_SUFFIX.get(
        path.suffix.lower(), "application/octet-stream"
    )


def avatar_filename(profile: Any) -> str:
    """Canonical published filename — basename of ``avatar_reference``."""
    reference = (profile.appearance.avatar_reference or "").strip()
    return PurePosixPath(reference).name


def build_avatar_delivery(
    profile: Any,
    service_root: Path,
    *,
    image_content_cls: Any | None = None,
) -> AvatarDelivery:
    """Build the canonical avatar delivery parts from the ficha.

    ``image_content_cls`` lets callers inject ``mcp.types.ImageContent``
    lazily (each owner pins its own SDK import); when ``None`` it is
    imported here.
    """
    path = approved_avatar_path(profile, service_root)
    if path is None:
        return AvatarDelivery(data=None, image=None, display_name=None)
    identity = profile.identity
    display_name = identity.display_name or identity.name
    content = path.read_bytes()
    mime = avatar_mime(path)
    too_large = len(content) > AVATAR_INLINE_MAX_BYTES
    data: dict[str, Any] = {
        "character_id": identity.character_id,
        "display_name": display_name,
        "avatar_status": profile.appearance.avatar_status,
        "avatar_reference": profile.appearance.avatar_reference,
        "mime_type": mime,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "content_delivery": "too_large" if too_large else "image_block",
    }
    if too_large:
        return AvatarDelivery(
            data=data,
            image=None,
            display_name=display_name,
            too_large=True,
        )
    if image_content_cls is None:
        from mcp.types import ImageContent as image_content_cls  # noqa: N811

    image = image_content_cls(
        type="image",
        data=base64.b64encode(content).decode("ascii"),
        mime_type=mime,
    )
    return AvatarDelivery(
        data=data, image=image, display_name=display_name
    )
