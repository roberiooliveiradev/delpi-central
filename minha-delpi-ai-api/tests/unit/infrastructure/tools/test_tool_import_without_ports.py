"""Import de tools/composição não pode depender de ports já configurados.

Regressão: description da tool TV resolvia conteúdo no corpo da classe e
quebrava o boot (`flask db upgrade`) antes de
`configure_domain_infrastructure_ports()`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[4]


def _import_in_clean_process(module: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        cwd=str(_PACKAGE_ROOT),
        capture_output=True,
        text=True,
        timeout=180,
    )


def test_tv_dashboard_copilot_tool_imports_without_ports():
    result = _import_in_clean_process("app.infrastructure.tools.tv_dashboard_copilot_tool")

    assert result.returncode == 0, result.stderr


def test_tool_composer_imports_without_ports():
    result = _import_in_clean_process("app.composition.tool_composer")

    assert result.returncode == 0, result.stderr
