"""Windows-side runner for the R09 Gate 041 probes (read-only).

Loads infra/.env (TOTVS_DB_* + DB_* settings) through python-dotenv —
values are never printed — then delegates to the parity probe. The SQL
Server is reachable through ODBC Driver 18 on the Windows host; the WSL
/docker route is unavailable in this session.

Usage:
    python r09_win_probe_runner.py <probe_script> <xlsb> <period>
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Load every candidate env file without echoing values; real secrets
# stay inside the process only.
for env_name in ("infra/.env", "api-delpi/.env", "infra/.env.local"):
    env_path = REPO / env_name
    if env_path.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path, override=False)
            print(f"[env] loaded {env_name} (values not shown)")
        except ImportError:
            print("[env] python-dotenv missing — install it")

sys.path.insert(0, str(REPO / "api-delpi"))
sys.path.insert(0, str(REPO / "shared"))

probe = Path(sys.argv[1]).resolve()
sys.argv = [str(probe)] + sys.argv[2:]
runpy.run_path(str(probe), run_name="__main__")
