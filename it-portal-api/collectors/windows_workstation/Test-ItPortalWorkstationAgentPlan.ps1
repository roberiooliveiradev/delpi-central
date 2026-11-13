#requires -Version 5.1
# G2-S3: smoke SEM efeitos colaterais; pode rodar no pwsh do CI Linux.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$base = $PSScriptRoot
$workstation = [guid]::Parse('2bb2c32d-d851-4e93-8f8a-cd845671c32a')
$inputs = @{
    ApiBaseUrl = 'https://example.invalid/apps/it-portal-api'
    S2sTokenUrl = 'https://example.invalid/auth/realms/test/protocol/openid-connect/token'
    ClientId = 'pc-lab-example'
    WorkstationId = $workstation
    ExpectedHostname = 'example-pc-01'
    IntervalMinutes = 60
}
$install = & (Join-Path $base 'Install-ItPortalWorkstationAgent.ps1') @inputs
if (@($install | Where-Object { $_ -match '^G2_S3_PLAN_ONLY' }).Count -ne 1) {
    throw 'InstallDefaultMustBePlanOnly'
}
if (@($install | Where-Object { $_ -match '^G2_S3_INSTALLED' }).Count -ne 0) {
    throw 'InstallMustNotRegisterWithoutActivate'
}
$enable = & (Join-Path $base 'Enable-ItPortalWorkstationAgent.ps1') -WorkstationId $workstation
if (@($enable | Where-Object { $_ -match '^G2_S3_ENABLE_PLAN' }).Count -ne 1) {
    throw 'EnableDefaultMustBePlanOnly'
}
$uninstall = & (Join-Path $base 'Uninstall-ItPortalWorkstationAgent.ps1') -WorkstationId $workstation
if (@($uninstall | Where-Object { $_ -match '^G2_S3_UNINSTALL_PLAN' }).Count -ne 1) {
    throw 'UninstallDefaultMustBePlanOnly'
}
Write-Output 'G2_S3_PLAN_TEST_OK'
