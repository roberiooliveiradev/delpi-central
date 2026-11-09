"""Resolve monorepo-rooted artifacts for DÉLIA tests.

In DEV compose, ``delia-api`` is often mounted at ``/app`` without the
rest of the monorepo. Canonical CI/DEV therefore either:

1. runs pytest from the monorepo checkout (``delia-api`` as cwd), or
2. mounts ``docs`` / ``plugins/delia`` and/or sets ``DELIA_MONOREPO_ROOT``.
"""

from __future__ import annotations

import os
from pathlib import Path


def monorepo_path(*parts: str) -> Path:
    """Return an existing path under the monorepo or well-known mounts."""
    relative = Path(*parts)
    candidates: list[Path] = []

    env = (os.getenv("DELIA_MONOREPO_ROOT") or "").strip()
    if env:
        candidates.append(Path(env).resolve() / relative)

    here = Path(__file__).resolve()
    for parent in here.parents:
        candidates.append(parent / relative)

    # Explicit compose mounts (infra/docker-compose.dev.yml)
    if parts and parts[0] == "docs":
        candidates.append(Path("/docs").joinpath(*parts[1:]))
    if parts and parts[0] == "plugins":
        candidates.append(Path("/plugins").joinpath(*parts[1:]))
        # plugins/delia is often mounted at /plugins/delia
        if len(parts) >= 2 and parts[1] == "delia":
            candidates.append(Path("/plugins/delia").joinpath(*parts[2:]))

    candidates.append(Path("/") / relative)

    for path in candidates:
        if path.exists():
            return path

    searched = ", ".join(str(c) for c in candidates[:8])
    raise FileNotFoundError(
        f"monorepo artifact not found: {relative} (searched: {searched}). "
        "Set DELIA_MONOREPO_ROOT or mount docs/ + plugins/delia."
    )
