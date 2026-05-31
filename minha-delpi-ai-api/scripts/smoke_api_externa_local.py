#!/usr/bin/env python3
"""Smoke rápido — homologação local só com api-externa (api-delpi off).

Configura o agente oficial e valida estoque + chips operacionais.

Uso:
  PYTHONPATH=. .venv/bin/python scripts/smoke_api_externa_local.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import time


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    existing = env.get("PYTHONPATH", "").strip()
    env["PYTHONPATH"] = app_root if not existing else f"{app_root}{os.pathsep}{existing}"
    return env


def main() -> int:
    failed = 0
    env = _subprocess_env()

    print("== Configurar providers (api-externa on, api-delpi off) ==")
    cfg = subprocess.run(
        [
            sys.executable,
            "scripts/upsert_agent_provider.py",
            "--provider",
            "api-externa",
            "--enabled",
            "true",
            "--provider",
            "api-delpi",
            "--enabled",
            "false",
        ],
        cwd=None,
        env=env,
    )
    if cfg.returncode != 0:
        return cfg.returncode

    pause = int(os.environ.get("SMOKE_RATE_LIMIT_PAUSE", "65"))

    scripts = [
        ("shortcut placeholders", "scripts/smoke_shortcut_placeholders.py"),
        ("operational routing", "scripts/smoke_operational_routing.py"),
        ("follow-up chips", "scripts/smoke_follow_up_chips.py"),
    ]
    for index, (label, script) in enumerate(scripts):
        if index > 0 and pause > 0:
            print(f"\n(pausa {pause}s — rate limit chat_messages)\n")
            time.sleep(pause)
        print(f"\n== {label} ==")
        result = subprocess.run([sys.executable, script], check=False, env=env)
        if result.returncode != 0:
            failed += 1

    if failed:
        print(f"\n{failed} smoke(s) falharam", file=sys.stderr)
        return 1

    print("\nSmoke api-externa local: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
