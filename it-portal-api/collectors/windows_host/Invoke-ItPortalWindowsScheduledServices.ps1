#requires -Version 5.1
<#
.SYNOPSIS
  Executa inventario SCM periodicamente pelo Agendador, sem interacao.
.DESCRIPTION
  Somente leitura. Usa credencial DPAPI da mesma conta Windows que executa
  a tarefa. Nao registra segredo, JWT, payload nem mensagens HTTP.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https://[^\s"]+$')]
    [string]$ApiBaseUrl,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https://[^\s"]+$')]
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

$sender = Join-Path $PSScriptRoot 'Send-ItPortalWindowsServices.ps1'
$startedAt = Get-Date
$status = 'failed'
$runId = ''
$batches = 0
$httpStatus = ''
$errorType = ''
$exitCode = 1

try {
    if (-not [IO.Path]::IsPathRooted($SecretFile)) { throw 'SecretPathNotAbsolute' }
    if (-not (Test-Path -LiteralPath $sender -PathType Leaf)) { throw 'SenderMissing' }
    $sent = & $sender -ApiBaseUrl $ApiBaseUrl -S2sTokenUrl $S2sTokenUrl -ClientId $ClientId -ServerId $ServerId -ClientSecretDpapiPath $SecretFile
    if ($null -eq $sent -or $sent.status -ne 'enviado') {
        throw 'UnexpectedSenderResult'
    }
    $status = 'ok'
    $runId = [string]$sent.run_id
    $batches = [int]$sent.batches
    $exitCode = 0
} catch {
    # Evitar registrar a mensagem da excecao ou o corpo de respostas HTTP.
    $errorType = $_.Exception.GetType().Name
    if ($_.Exception -is [System.Net.WebException] -and $null -ne $_.Exception.Response) {
        try { $httpStatus = [string][int]$_.Exception.Response.StatusCode }
        catch { $httpStatus = '' }
    }
}

# Rotacao local limitada: log atual de 1 MiB + apenas um anterior.
# Usa pasta separada da coleta E4.S4 para nao misturar registros.
$logDir = Join-Path $PSScriptRoot 'logs'
$log = Join-Path $logDir 'runs.csv'
$oldLog = Join-Path $logDir 'runs.previous.csv'
try {
    if (-not (Test-Path -LiteralPath $logDir -PathType Container)) {
        New-Item -Path $logDir -ItemType Directory -Force | Out-Null
    }
    if ((Test-Path -LiteralPath $log -PathType Leaf) -and
        (Get-Item -LiteralPath $log).Length -gt 1MB) {
        Move-Item -LiteralPath $log -Destination $oldLog -Force
    }
    [pscustomobject]@{
        at = $startedAt.ToString('o')
        status = $status
        run_id = $runId
        batches = $batches
        duration_seconds = [math]::Round(((Get-Date) - $startedAt).TotalSeconds, 2)
        http_status = $httpStatus
        error_type = $errorType
    } | Export-Csv -LiteralPath $log -NoTypeInformation -Append -Encoding UTF8
} catch {
    # Falha de logging nao pode resultar em aparente sucesso operacional.
    $exitCode = 1
    $status = 'log_failed'
}

Write-Output ("IT_PORTAL_WINDOWS_SERVICES status={0} batches={1} run_id={2}" -f $status, $batches, $runId)
exit $exitCode
