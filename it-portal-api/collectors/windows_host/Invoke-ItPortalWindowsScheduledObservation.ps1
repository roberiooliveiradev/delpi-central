#requires -Version 5.1
<#
.SYNOPSIS
  Executa envio Windows E4.S4 sem prompt e registra apenas metadados de status.
.DESCRIPTION
  Para uso no Agendador de Tarefas sob a MESMA conta que criou o segredo DPAPI.
  Nao registra JSON de inventario, tokens, credenciais ou mensagens brutas HTTP.
  Nao modifica configuracoes do Windows, banco, servicos ou firewall.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https://')]
    [string]$ApiBaseUrl,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https://')]
    [string]$S2sTokenUrl,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9_.-]{3,100}$')]
    [string]$ClientId,

    [Parameter(Mandatory = $true)]
    [guid]$ServerId,

    [Parameter(Mandatory = $true)]
    [string]$SecretFile
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$sender = Join-Path $PSScriptRoot 'Send-ItPortalWindowsObservation.ps1'
$stamp = (Get-Date).ToString('yyyy-MM-ddTHH:mm:sszzz')
$status = 'failed'
$collected = ''
$runId = ''
$httpStatus = ''
$errorType = ''
$exitCode = 1

try {
    if (-not (Test-Path -LiteralPath $sender -PathType Leaf)) {
        throw 'SenderMissing'
    }
    $sent = & $sender -ApiBaseUrl $ApiBaseUrl -S2sTokenUrl $S2sTokenUrl `
        -ClientId $ClientId -ServerId $ServerId -ClientSecretDpapiPath $SecretFile
    if ($null -eq $sent -or $sent.status -ne 'enviado') {
        throw 'UnexpectedSenderResult'
    }
    $status = 'ok'
    $collected = [string]$sent.collected_status
    $runId = [string]$sent.run_id
    $exitCode = 0
} catch {
    # Nao registrar Exception.Message / response body: podem conter dados do host.
    $errorType = $_.Exception.GetType().Name
    if ($_.Exception -is [System.Net.WebException] -and $null -ne $_.Exception.Response) {
        try {
            $httpStatus = [string][int]$_.Exception.Response.StatusCode
        } catch {
            $httpStatus = ''
        }
    }
}

# CSV minimo, armazenado apenas no perfil local da conta da tarefa.
# Rotacao limitada: ate 1 MiB no log principal e 1 arquivo anterior.
$logDir = Join-Path $PSScriptRoot 'logs'
$log = Join-Path $logDir 'runs.csv'
$oldLog = Join-Path $logDir 'runs.previous.csv'
if (-not (Test-Path -LiteralPath $logDir -PathType Container)) {
    New-Item -Path $logDir -ItemType Directory -Force | Out-Null
}
if ((Test-Path -LiteralPath $log -PathType Leaf) -and
    (Get-Item -LiteralPath $log).Length -gt 1MB) {
    Move-Item -LiteralPath $log -Destination $oldLog -Force
}
[pscustomobject]@{
    at = $stamp
    status = $status
    collected_status = $collected
    run_id = $runId
    http_status = $httpStatus
    error_type = $errorType
} | Export-Csv -LiteralPath $log -NoTypeInformation -Append -Encoding UTF8

Write-Output ("IT_PORTAL_WINDOWS status={0} http={1} run_id={2}" -f $status, $httpStatus, $runId)
exit $exitCode
