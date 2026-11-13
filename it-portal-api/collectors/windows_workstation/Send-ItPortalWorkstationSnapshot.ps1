#requires -Version 5.1
<#
.SYNOPSIS
  G2-S2: envia snapshot manual de uma estacao Windows, SOMENTE apos enrolment S2S.
.DESCRIPTION
  Nenhum servico/tarefa agendada; credencial exclusiva por computador
  protegida com DPAPI no usuario Windows autorizado. Nao salva token em disco.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^https://')][string]$ApiBaseUrl,
    [Parameter(Mandatory=$true)][ValidatePattern('^https://')][string]$S2sTokenUrl,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_.-]{3,100}$')][string]$ClientId,
    [Parameter(Mandatory=$true)][guid]$WorkstationId,
    [Parameter(Mandatory=$true)][string]$ClientSecretDpapiPath,
    [switch]$IncludePrivateIPv4
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not [IO.Path]::IsPathRooted($ClientSecretDpapiPath)) {
    throw 'Caminho DPAPI precisa ser absoluto.'
}
if (-not (Test-Path -LiteralPath $ClientSecretDpapiPath -PathType Leaf)) {
    throw 'Arquivo DPAPI de credencial individual ausente.'
}
$collector = Join-Path $PSScriptRoot 'Collect-ItPortalWorkstationSnapshot.ps1'
if (-not (Test-Path -LiteralPath $collector -PathType Leaf)) {
    throw 'Script local de coleta Windows ausente.'
}
$encrypted = (Get-Content -LiteralPath $ClientSecretDpapiPath -Raw -ErrorAction Stop).Trim()
$secretSecure = ConvertTo-SecureString -String $encrypted -ErrorAction Stop
$encrypted = $null
$ptr = [IntPtr]::Zero
try {
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretSecure)
    $secretPlain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    try {
        $tokenParams = @{
            Uri = $S2sTokenUrl
            Method = 'Post'
            ContentType = 'application/x-www-form-urlencoded'
            Body = @{
                grant_type = 'client_credentials'
                client_id = $ClientId
                client_secret = $secretPlain
            }
            MaximumRedirection = 0
            TimeoutSec = 20
            ErrorAction = 'Stop'
        }
        $tokenResponse = Invoke-RestMethod @tokenParams
    } finally {
        $secretPlain = $null
    }
} finally {
    if ($ptr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
    $secretSecure.Dispose()
}
if (-not $tokenResponse.access_token) { throw 'S2S nao retornou access_token.' }

$json = & $collector -IncludePrivateIPv4:$IncludePrivateIPv4
if (-not $json) { throw 'Coletor local nao retornou inventario.' }
$payload = [string]$json
$runId = ([guid]([string](($payload | ConvertFrom-Json -ErrorAction Stop).run_id))).ToString()
$bytes = [Text.Encoding]::UTF8.GetBytes($payload)
if ($bytes.Length -gt 32768) { throw 'Snapshot excedeu 32 KiB.' }
$url = '{0}/collector/v1/workstations/{1}/snapshots' -f $ApiBaseUrl.TrimEnd('/'), $WorkstationId.ToString()
try {
    $sendParams = @{
        Uri = $url
        Method = 'Post'
        ContentType = 'application/json; charset=utf-8'
        Headers = @{ 'X-Delpi-Service-Authorization' = "Bearer $($tokenResponse.access_token)" }
        Body = $bytes
        MaximumRedirection = 0
        TimeoutSec = 30
        ErrorAction = 'Stop'
    }
    $response = Invoke-RestMethod @sendParams
} finally {
    $tokenResponse = $null
}
if (-not $response.success -or -not $response.data) {
    throw 'API nao confirmou recebimento.'
}
if ([string]$response.data.workstation_id -ne $WorkstationId.ToString() -or
    [string]$response.data.run_id -ne $runId) {
    throw 'Resposta da API nao corresponde ao computador ou a coleta.'
}
[pscustomobject]@{
    status = if ($response.data.duplicate) { 'duplicado' } else { 'enviado' }
    run_id = $runId
    workstation_id = $WorkstationId.ToString()
}
