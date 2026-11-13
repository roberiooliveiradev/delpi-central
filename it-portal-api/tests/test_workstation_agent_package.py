"""G2-S3: guardas do pacote Windows, sem contato com computadores reais."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "collectors" / "windows_workstation"

FILES = {
    "installer": "Install-ItPortalWorkstationAgent.ps1",
    "runner": "Invoke-ItPortalWorkstationScheduledSnapshot.ps1",
    "enable": "Enable-ItPortalWorkstationAgent.ps1",
    "uninstaller": "Uninstall-ItPortalWorkstationAgent.ps1",
    "plan_test": "Test-ItPortalWorkstationAgentPlan.ps1",
    "collector": "Collect-ItPortalWorkstationSnapshot.ps1",
    "sender": "Send-ItPortalWorkstationSnapshot.ps1",
}


def read(name):
    return (ROOT / FILES[name]).read_text("utf-8")


def test_g2_s3_package_contains_no_hardcoded_identity_or_secret():
    for name in FILES:
        script = read(name)
        assert "#requires -Version 5.1" in script
        assert "ExecutionPolicy Bypass" not in script
        assert "Register-PSSessionConfiguration" not in script
        assert "New-PSSession" not in script
        assert "Enable-PSRemoting" not in script
        assert "password=" not in script.lower()
        assert "client_secret=" not in script.lower()
    for name in ("installer", "runner", "enable", "uninstaller"):
        assert "RemoteDesktop" not in read(name)


def test_installer_requires_human_gate_signature_and_dpapi():
    script = read("installer")
    assert "if (-not $Activate) { return }" in script
    assert "Get-AuthenticodeSignature" in script
    assert "UntrustedCodeSignature" in script
    assert "HostnameMismatch" in script
    assert "ConvertFrom-SecureString" in script
    assert "New-ScheduledTaskSettingsSet -Disable" in script
    assert "-LogonType Interactive" in script
    assert "Register-ScheduledTask" in script
    assert "G2_S3_INSTALLED_DISABLED" in script
    assert "Read-Host" in script
    assert "Remove-Item -LiteralPath $installDir" in script


def test_runner_never_logs_payload_or_http_errors():
    script = read("runner")
    assert "Get-AuthenticodeSignature" in script
    assert "Send-ItPortalWorkstationSnapshot.ps1" in script
    assert "HostnameMismatch" in script
    assert "runs.previous.csv" in script
    assert "error_type = $errorType" in script
    assert "response_body" not in script
    assert "Authorization" not in script
    assert "Register-ScheduledTask" not in script
    assert "Invoke-Expression" not in script


def test_enable_requires_smoke_and_uninstaller_requires_revocation():
    enabled = read("enable")
    uninstall = read("uninstaller")
    assert "if (-not $Activate)" in enabled
    assert "Get-AuthenticodeSignature" in enabled
    assert "Send-ItPortalWorkstationSnapshot.ps1" in enabled
    assert "Enable-ScheduledTask" in enabled
    assert "Disable-ScheduledTask" in enabled
    assert "if (-not $Activate)" in uninstall
    assert "if (-not $RevokedInKeycloak -or -not $BindingRemoved)" in uninstall
    assert "Unregister-ScheduledTask" in uninstall
    assert "Remove-Item -LiteralPath $installDir" in uninstall


def test_automation_is_logon_scoped_and_not_silently_unattended():
    assert "-LogonType Interactive" in read("installer")
    assert "client-secret.dpapi" in read("installer")
    assert "-LogonType Password" not in read("installer")
    assert "-User $identity.Name -Password" not in read("installer")
    assert "Start-ScheduledTask" not in read("installer")
    assert "ScheduledTask -TaskName" not in read("plan_test")
