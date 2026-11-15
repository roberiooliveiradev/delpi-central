#requires -Version 5.1
# CI smoke: no Windows mutation; probe must be untrusted/read-only.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$path = Join-Path $PSScriptRoot 'Collect-ItPortalWorkstationTrustReadiness.ps1'

# Forbid network, registration, certificate or key-management operations.
$source = [System.IO.File]::ReadAllText($path)
$disallowed = @(
    'Invoke-RestMethod', 'Invoke-WebRequest', 'Invoke-Command', 'New-PSSession',
    'Set-Tpm', 'Clear-Tpm', 'Initialize-Tpm', 'Disable-TpmAutoProvisioning',
    'New-SelfSignedCertificate', 'New-Item', 'Set-Item', 'Set-Content',
    'Add-Content', 'Out-File', 'Export-', 'Start-Process',
    'Register-ScheduledTask', 'Set-ScheduledTask', 'Enable-ScheduledTask',
    'Set-ExecutionPolicy', 'Add-MpPreference', 'Set-MpPreference'
)
foreach ($name in $disallowed) {
    $pattern = '(?i)(?<![A-Za-z0-9_-])' + [regex]::Escape($name)
    if ($source -match $pattern) {
        throw "P4_ForbiddenCommand_$name"
    }
}
$raw = & $path
$data = $raw | ConvertFrom-Json
if ($data.schema_version -ne 1 -or $data.kind -ne 'delpi-it-remote-p4-readiness') {
    throw 'P4_SchemaMismatch'
}
if ($data.origin -ne 'unauthenticated-local-readonly') { throw 'P4_OriginMustBeUntrusted' }
if ($data.activation_authorized -ne $false -or $data.hardware_attested -ne $false -or $data.key_bound -ne $false) {
    throw 'P4_ProbeMustNeverAuthorizeEnrollment'
}
if ($data.tpm.present -notin @('yes','no','unknown') -or
    $data.tpm.ready -notin @('yes','no','unknown') -or
    $data.tpm.spec -notin @('2.0','1.2','unknown') -or
    $data.secure_boot -notin @('enabled','disabled','unknown')) {
    throw 'P4_UnexpectedProbeState'
}
$allowedFields = @('schema_version','kind','origin','collected_at','platform','tpm',
                   'secure_boot','hardware_attested','key_bound','activation_authorized')
if (@($data.PSObject.Properties.Name).Count -ne $allowedFields.Count) {
    throw 'P4_PrivacySchemaMustBeMinimal'
}
if ($env:OS -ne 'Windows_NT' -and $data.platform -ne 'non_windows') {
    throw 'P4_LinuxMustBeNonWindows'
}
Write-Output 'G2_S4_S2B_P4_READONLY_SMOKE_OK'
