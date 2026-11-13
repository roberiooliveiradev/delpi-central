"""Guarda basica para o atualizador do agente Windows instalado.

A compilacao de PowerShell roda no CI GitHub Ubuntu com pwsh. Nenhuma tarefa
agendada ou servico Windows e instalado ou alterado neste teste.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "collectors/windows_host/Update-ItPortalWindowsServiceControlAgent.ps1"
)


def test_update_script_exists_with_dry_run_default() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "[switch]$Activate" in text
    assert "if (-not $Activate)" in text
    assert "Export-ScheduledTask" in text
    assert "Stop-ScheduledTask" in text
    assert "Set-ScheduledTask" in text
    assert "Start-ScheduledTask" in text
    assert "25" in text
    assert "client-secret.dpapi" in text


def test_update_script_parses_in_pwsh() -> None:
    exe = shutil.which("pwsh")
    if exe is None:
        pytest.skip("pwsh indisponivel no ambiente")
    command = (
        "$tokens=$null; $errors=$null; "
        "[void][System.Management.Automation.Language.Parser]::ParseFile("
        "$args[0],[ref]$tokens,[ref]$errors); "
        "if ($errors.Count) { $errors | Out-String | Write-Error; exit 1 }"
    )
    completed = subprocess.run(
        [exe, "-NoProfile", "-Command", command, str(SCRIPT)],
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
