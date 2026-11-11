#requires -Version 5.1
<#
.SYNOPSIS
  Publica uma observação Windows local no Portal de TI (smoke manual E4.S3).
.DESCRIPTION
  Executa o coletor read-only existente, obtém token S2S via Keycloak
  client_credentials e envia para a API por HTTPS. Não agenda tarefas, não
  cria arquivos nem imprime segredos ou o JSON técnico completo.
  Use cliente confidencial exclusivo do host, escopo it-portal.observations.ingest
  e audience it-portal-api. O secret é solicitado interativamente, ou lido
  de um arquivo DPAPI criado pela mesma conta Windows que executa a tarefa.
.EXAMPLE
  .\Send-ItPortalWindowsObservation.ps1 -ApiBaseUrl 'https://portal.exemplo/apps/it-portal-api' -S2sTokenUrl 'https://auth.exemplo/realms/delpi/protocol/openid-connect/token' -ClientId 'it-portal-windows-pilot01' -ServerId '<uuid-cadastrado>'
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

    [string[]]$ServiceNames = @('EventLog', 'W32Time', 'LanmanServer'),

    [string]$ClientSecretDpapiPath
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$collector = Join-Path $PSScriptRoot 'Collect-ItPortalWindowsInventory.ps1'
if (-not (Test-Path -LiteralPath $collector -PathType Leaf)) {
    throw 'Coletor local não encontrado ao lado do publicador.'
}

# Uma observação = um run_id; nunca armazenar o JSON técnico em arquivo local.
$raw = & $collector -ServiceNames $ServiceNames
if (-not $raw -or $raw -is [array]) {
    throw 'Coletor não retornou um único JSON válido.'
}
$observation = $raw | ConvertFrom-Json -ErrorAction Stop
if ($observation.source -ne 'windows_host_collector' -or -not $observation.run_id) {
    throw 'Origem ou run_id inválidos no diagnóstico local.'
}

# Para o agendador, apenas o usuario que cifrou via DPAPI neste host pode
# descriptografar. Nenhum segredo aparece nos argumentos, logs ou arquivos .ps1.
$secureSecret = $null
if ($ClientSecretDpapiPath) {
    if (-not [System.IO.Path]::IsPathRooted($ClientSecretDpapiPath) -or
        -not (Test-Path -LiteralPath $ClientSecretDpapiPath -PathType Leaf)) {
        throw 'Arquivo DPAPI local nao encontrado (caminho absoluto obrigatorio).'
    }
    try {
        $encryptedSecret = (Get-Content -LiteralPath $ClientSecretDpapiPath -Raw -ErrorAction Stop).Trim()
        if (-not $encryptedSecret) {
            throw 'Conteudo DPAPI vazio.'
        }
        $secureSecret = ConvertTo-SecureString -String $encryptedSecret -ErrorAction Stop
    } catch {
        throw 'Nao foi possivel ler o segredo DPAPI: execute com a mesma conta e no mesmo Windows usado na criacao.'
    } finally {
        $encryptedSecret = $null
    }
} else {
    $secureSecret = Read-Host -Prompt "Client secret S2S de $ClientId (não aparece na tela)" -AsSecureString
}
$handle = [IntPtr]::Zero
$clientSecret = $null
try {
    $handle = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureSecret)
    $clientSecret = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($handle)
    if ([string]::IsNullOrWhiteSpace($clientSecret)) {
        throw 'Client secret vazio.'
    }
    # Parâmetros via body, jamais query string, stdout ou histórico de comandos.
    $tokenResponse = Invoke-RestMethod -Uri $S2sTokenUrl -Method Post -ContentType 'application/x-www-form-urlencoded' -Body @{
        grant_type = 'client_credentials'
        client_id = $ClientId
        client_secret = $clientSecret
    } -TimeoutSec 30 -ErrorAction Stop
} finally {
    $clientSecret = $null
    if ($handle -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($handle)
    }
    if ($null -ne $secureSecret) {
        $secureSecret.Dispose()
    }
}

if (-not $tokenResponse.access_token) {
    throw 'O provedor S2S não retornou access_token.'
}

$uri = '{0}/collector/v1/servers/{1}/observations' -f $ApiBaseUrl.TrimEnd('/'), $ServerId
$response = Invoke-RestMethod -Uri $uri -Method Post -ContentType 'application/json' -Headers @{
    'X-Delpi-Service-Authorization' = "Bearer $($tokenResponse.access_token)"
} -Body $raw -TimeoutSec 30 -ErrorAction Stop

if (-not $response.data -or $response.data.run_id -ne $observation.run_id) {
    throw 'Resposta de ingestão inesperada; conferir API antes de repetir.'
}
[pscustomobject]@{
    status = 'enviado'
    source = $observation.source
    run_id = $observation.run_id
    collected_status = $observation.status
}
