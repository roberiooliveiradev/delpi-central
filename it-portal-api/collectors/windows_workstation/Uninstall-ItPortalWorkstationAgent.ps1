#requires -Version 5.1
<#
.SYNOPSIS
 G2-S3: remove a tarefa e o pacote Windows apos revogacao do cliente S2S.
.DESCRIPTION
 Sem -Activate: somente plano. Para remocao efetiva exige que a identidade
 Keycloak tenha sido revogada e o binding removido da configuracao privada.
 Nao altera outros agentes ou tarefas da maquina.
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory = $true)][guid]$WorkstationId,
    [switch]$RevokedInKeycloak,
    [switch]$BindingRemoved,
    [switch]$Activate
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($WorkstationId -eq [guid]::Empty) { throw 'WorkstationIdObrigatorio' }
$taskName = 'Delpi-PortalTI-WorkstationInventory-' + $WorkstationId.ToString('N')
Write-Output ('G2_S3_UNINSTALL_PLAN task={0}' -f $taskName)
if (-not $Activate) { Write-Output 'Somente planejamento, nenhuma remocao efetuada.'; return }
if (-not $RevokedInKeycloak -or -not $BindingRemoved) {
    throw 'Revogar cliente Keycloak e remover binding antes da desinstalacao.'
}
if ($PSVersionTable.PSEdition -ne 'Desktop') { throw 'WindowsPowerShell51Required' }
if (-not $env:LOCALAPPDATA -or -not [IO.Path]::IsPathRooted($env:LOCALAPPDATA) -or $env:LOCALAPPDATA.StartsWith('\\')) {
    throw 'LocalAppDataInvalid'
}
Import-Module ScheduledTasks -ErrorAction Stop
$installDir = Join-Path $env:LOCALAPPDATA ('Delpi\PortalTI\Workstations\{0}' -f $WorkstationId.ToString('N'))
$configPath = Join-Path $installDir 'settings.json'
if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw 'InstalacaoNaoEncontradaOuIncompleta'
}
$config = Get-Content -LiteralPath $configPath -Raw -ErrorAction Stop | ConvertFrom-Json
if ([string]$config.workstation_id -ne $WorkstationId.ToString() -or
    [string]$config.task_name -ne $taskName -or
    [string]$config.expected_hostname -ne [Environment]::MachineName.ToLowerInvariant()) {
    throw 'IdentidadeDoPacoteDivergente'
}
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
if ($task.Principal.UserId -ne $sid -or $task.Actions.Count -ne 1 -or
    -not $task.Actions[0].Arguments.Contains((Join-Path $installDir 'Invoke-ItPortalWorkstationScheduledSnapshot.ps1'))) {
    throw 'TarefaNaoCorrespondeAoPacote'
}
if (-not $PSCmdlet.ShouldProcess($taskName, 'Desabilitar, remover tarefa e apagar pacote DPAPI local')) {
    return
}
Disable-ScheduledTask -TaskName $taskName -ErrorAction Stop | Out-Null
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
Remove-Item -LiteralPath $installDir -Recurse -Force -ErrorAction Stop
Write-Output ('G2_S3_UNINSTALLED task={0}' -f $taskName)
Write-Output 'A credencial Keycloak precisa continuar revogada; exclusao local nao revoga tokens ativos.'
