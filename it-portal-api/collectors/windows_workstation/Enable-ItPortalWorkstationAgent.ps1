#requires -Version 5.1
<#
.SYNOPSIS
 G2-S3: habilita tarefa de inventario instalada, apos NOVO smoke S2S.
.DESCRIPTION
 Sem -Activate: somente plano. Somente conta que cifrou DPAPI pode habilitar.
 Funciona enquanto esta conta estiver conectada no Windows; nao e um servico.
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory = $true)][guid]$WorkstationId,
    [switch]$Activate
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($WorkstationId -eq [guid]::Empty) { throw 'WorkstationIdObrigatorio' }
$taskName = 'Delpi-PortalTI-WorkstationInventory-' + $WorkstationId.ToString('N')
Write-Output ('G2_S3_ENABLE_PLAN task={0}' -f $taskName)
if (-not $Activate) { Write-Output 'Somente planejamento: use -Activate apos validacao presencial.'; return }

if ($PSVersionTable.PSEdition -ne 'Desktop') { throw 'WindowsPowerShell51Required' }
if (-not $env:LOCALAPPDATA -or -not [IO.Path]::IsPathRooted($env:LOCALAPPDATA) -or $env:LOCALAPPDATA.StartsWith('\\')) {
    throw 'LocalAppDataInvalid'
}
Import-Module ScheduledTasks -ErrorAction Stop
$installDir = Join-Path $env:LOCALAPPDATA ('Delpi\PortalTI\Workstations\{0}' -f $WorkstationId.ToString('N'))
$configFile = Join-Path $installDir 'settings.json'
$secretFile = Join-Path $installDir 'client-secret.dpapi'
if (-not (Test-Path -LiteralPath $configFile -PathType Leaf) -or
    -not (Test-Path -LiteralPath $secretFile -PathType Leaf)) {
    throw 'PackageOrSecretMissing'
}
$config = Get-Content -LiteralPath $configFile -Raw | ConvertFrom-Json
if ([string]$config.workstation_id -ne $WorkstationId.ToString() -or
    [string]$config.task_name -ne $taskName -or
    [string]$config.expected_hostname -ne [Environment]::MachineName.ToLowerInvariant()) {
    throw 'PackageIdentityMismatch'
}
$signer = ([string]$config.trusted_signer_thumbprint).ToUpperInvariant()
if ($signer -notmatch '^[A-F0-9]{40}$') { throw 'SignerMissing' }
foreach ($path in @(
    $PSCommandPath,
    (Join-Path $installDir 'Collect-ItPortalWorkstationSnapshot.ps1'),
    (Join-Path $installDir 'Send-ItPortalWorkstationSnapshot.ps1'),
    (Join-Path $installDir 'Invoke-ItPortalWorkstationScheduledSnapshot.ps1')
)) {
    $sig = Get-AuthenticodeSignature -FilePath $path -ErrorAction Stop
    if ($sig.Status -ne 'Valid' -or $null -eq $sig.SignerCertificate -or
        $sig.SignerCertificate.Thumbprint.ToUpperInvariant() -ne $signer) {
        throw 'PackageSignatureInvalid'
    }
}
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
if ($task.State -ne 'Disabled') { throw 'TaskNotDisabled' }
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
if ($task.Principal.UserId -ne $sid) { throw 'TaskPrincipalMismatch' }
if ($task.Actions.Count -ne 1 -or
    -not $task.Actions[0].Arguments.Contains((Join-Path $installDir 'Invoke-ItPortalWorkstationScheduledSnapshot.ps1'))) {
    throw 'TaskActionMismatch'
}
if (-not $PSCmdlet.ShouldProcess($taskName, 'Validar S2S e habilitar coleta agendada')) { return }

try {
    $sendArgs = @{
        ApiBaseUrl = [string]$config.api_base_url
        S2sTokenUrl = [string]$config.s2s_token_url
        ClientId = [string]$config.client_id
        WorkstationId = $WorkstationId
        ClientSecretDpapiPath = $secretFile
        IncludePrivateIPv4 = [bool]$config.include_private_ipv4
    }
    $smoke = & (Join-Path $installDir 'Send-ItPortalWorkstationSnapshot.ps1') @sendArgs
    if ($null -eq $smoke -or $smoke.status -ne 'enviado') { throw 'SmokeFailed' }
    Enable-ScheduledTask -TaskName $taskName -ErrorAction Stop | Out-Null
    if ((Get-ScheduledTask -TaskName $taskName -ErrorAction Stop).State -eq 'Disabled') {
        throw 'EnableDidNotTakeEffect'
    }
    Write-Output ('G2_S3_ENABLED task={0}' -f $taskName)
} catch {
    Disable-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue | Out-Null
    throw 'G2_S3_ENABLE_ABORTED: tarefa desabilitada; revisar piloto localmente.'
}
