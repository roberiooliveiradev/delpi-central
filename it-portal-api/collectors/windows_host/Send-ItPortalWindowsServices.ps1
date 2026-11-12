#requires -Version 5.1
<#
.SYNOPSIS
  Envia lotes Windows SCM por HTTPS, autenticacao S2S exclusiva.
.DESCRIPTION
  Requer escopo it-portal.host-services.ingest; nunca altera servicos.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^https://')][string]$ApiBaseUrl,
    [Parameter(Mandatory=$true)][ValidatePattern('^https://')][string]$S2sTokenUrl,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_.-]{3,100}$')][string]$ClientId,
    [Parameter(Mandatory=$true)][guid]$ServerId,
    [ValidateRange(1,100)][int]$BatchSize = 100,
    [string]$ClientSecretDpapiPath
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$collector = Join-Path $PSScriptRoot 'Collect-ItPortalWindowsServices.ps1'
if (-not (Test-Path -LiteralPath $collector -PathType Leaf)) { throw 'Coletor SCM ausente.' }
$secure = $null
if ($ClientSecretDpapiPath) {
    if (-not [IO.Path]::IsPathRooted($ClientSecretDpapiPath)) { throw 'Caminho DPAPI invalido.' }
    $encrypted = (Get-Content -LiteralPath $ClientSecretDpapiPath -Raw -ErrorAction Stop).Trim()
    $secure = ConvertTo-SecureString -String $encrypted -ErrorAction Stop
    $encrypted = $null
} else {
    $secure = Read-Host -Prompt "Client Secret Keycloak de $ClientId" -AsSecureString
}
$ptr = [IntPtr]::Zero
try {
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $secret = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    $tokenResponse = Invoke-RestMethod -Uri $S2sTokenUrl -Method Post -ContentType 'application/x-www-form-urlencoded' -Body @{ grant_type='client_credentials'; client_id=$ClientId; client_secret=$secret } -TimeoutSec 30 -ErrorAction Stop
} finally {
    $secret = $null
    if ($ptr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
    if ($null -ne $secure) { $secure.Dispose() }
}
if (-not $tokenResponse.access_token) { throw 'Autenticacao S2S falhou.' }
$uri = '{0}/collector/v1/servers/{1}/host-services/batches' -f $ApiBaseUrl.TrimEnd('/'), $ServerId
$payloads = @(& $collector -BatchSize $BatchSize)
if ($payloads.Count -lt 1) { throw 'Coleta sem lotes.' }
$runId = ''
$lastStatus = ''
foreach ($json in $payloads) {
    $batch = $json | ConvertFrom-Json -ErrorAction Stop
    if (-not $runId) { $runId = [string]$batch.run_id }
    if ([string]$batch.run_id -ne $runId) { throw 'Run ID inconsistente.' }
    $response = Invoke-RestMethod -Uri $uri -Method Post -ContentType 'application/json; charset=utf-8' -Headers @{ 'X-Delpi-Service-Authorization' = "Bearer $($tokenResponse.access_token)" } -Body ([Text.Encoding]::UTF8.GetBytes($json)) -TimeoutSec 30 -ErrorAction Stop
    if (-not $response.data -or $response.data.run_id -ne $runId) { throw 'Resposta inesperada da API.' }
    $lastStatus = [string]$response.data.status
}
if ($lastStatus -ne 'complete') { throw 'Inventario nao consolidado.' }
[pscustomobject]@{ status='enviado'; run_id=$runId; batches=$payloads.Count }
