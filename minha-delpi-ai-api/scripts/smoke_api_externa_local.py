#!/usr/bin/env python3
"""Smoke rápido — homologação local só com api-externa (api-delpi off).

Configura o agente oficial e valida estoque + chips operacionais.

Uso:
  PYTHONPATH=. .venv/bin/python scripts/smoke_api_externa_local.py
"""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    failed = 0

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
    )
    if cfg.returncode != 0:
        return cfg.returncode

    for label, script in [
        ("operational routing", "scripts/smoke_operational_routing.py"),
        ("follow-up chips", "scripts/smoke_follow_up_chips.py"),
    ]:
        print(f"\n== {label} ==")
        result = subprocess.run([sys.executable, script], check=False)
        if result.returncode != 0:
            failed += 1

    if failed:
        print(f"\n{failed} smoke(s) falharam", file=sys.stderr)
        return 1

    print("\nSmoke api-externa local: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
