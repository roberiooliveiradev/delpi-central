from __future__ import annotations

import os
from pathlib import Path


def load_env_file(path: str | None = None) -> None:
    env_path = Path(path or os.getenv("ENV_FILE") or "")

    if not env_path:
        return

    if not env_path.exists() or not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value
