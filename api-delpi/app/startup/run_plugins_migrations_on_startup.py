# app/startup/run_plugins_migrations_on_startup.py
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def run_plugins_migrations_on_startup() -> None:
    enabled = os.getenv("RUN_PLUGINS_MIGRATIONS_ON_STARTUP", "false").lower() == "true"
    if not enabled:
        return

    project_root = Path(__file__).resolve().parents[2]
    script_path = project_root / "scripts" / "run_plugins_migrations.py"

    if not script_path.exists():
        raise RuntimeError(f"Migration script não encontrado: {script_path}")

    result = subprocess.run(
        ["python", str(script_path), "up"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Falha ao executar migrations de plugins no startup.\n"
            f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )

    print(result.stdout)