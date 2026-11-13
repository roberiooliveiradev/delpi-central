#requires -Version 5.1
<#
.SYNOPSIS
  G2-S3: execucao agendada local do inventario de uma workstation corporativa.
.DESCRIPTION
  Executa somente a coleta Windows G2-S1 e o envio S2S G2-S2.
  Nunca registra tokens, dados do inventario ou texto de erros HTTP nos logs.
  Depende de configuracao protegida e assinatura validada dos scripts.
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$startedAt = Get-Date
$code = 1
$status = 'failed'
$runId = ''
$errorType = ''

try {
    $configPath = Join-Path $PSScriptRoot 'settings.json'
    if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
        throw 'SettingsMissing'
    }
    $config = Get-Content -LiteralPath $configPath -Raw -ErrorAction Stop |
        ConvertFrom-Json -ErrorAction Stop
    $expectedId = [guid]([string]$config.workstation_id)
    if ($expectedId -eq [guid]::Empty) { throw 'WorkstationIdInvalid' }
    $expectedHost = ([string]$config.expected_hostname).Trim().ToLowerInvariant()
    if ([Environment]::MachineName.ToLowerInvariant() -ne $expectedHost) {
        throw 'HostnameMismatch'
    }
    $thumbprint = ([string]$config.trusted_signer_thumbprint).Replace(' ', '').ToUpperInvariant()
    if ($thumbprint -notmatch '^[A-F0-9]{40}$') { throw 'TrustedSignerMissing' }

    $collector = Join-Path $PSScriptRoot 'Collect-ItPortalWorkstationSnapshot.ps1'
    $sender = Join-Path $PSScriptRoot 'Send-ItPortalWorkstationSnapshot.ps1'
    foreach ($scriptPath in @($collector, $sender, $PSCommandPath)) {
        $signature = Get-AuthenticodeSignature -FilePath $scriptPath -ErrorAction Stop
        if ($signature.Status -ne 'Valid' -or $null -eq $signature.SignerCertificate -or
            $signature.SignerCertificate.Thumbprint.ToUpperInvariant() -ne $thumbprint) {
            throw 'ScriptSignatureInvalid'
        }
    }

    $secretPath = Join-Path $PSScriptRoot 'client-secret.dpapi'
    if (-not (Test-Path -LiteralPath $secretPath -PathType Leaf)) {
        throw 'SecretMissing'
    }
    $params = @{
        ApiBaseUrl = [string]$config.api_base_url
        S2sTokenUrl = [string]$config.s2s_token_url
        ClientId = [string]$config.client_id
        WorkstationId = $expectedId
        ClientSecretDpapiPath = $secretPath
        IncludePrivateIPv4 = [bool]$config.include_private_ipv4
    }
    $sent = & $sender @params
    if ($null -eq $sent -or $sent.status -notin @('enviado', 'duplicado')) {
        throw 'UnexpectedSenderResult'
    }
    $status = 'ok'
    $runId = [string]$sent.run_id
    $code = 0
} catch {
    # Excecoes de rede podem conter endpoint, request ou token. Nao registrar mensagem.
    $errorType = $_.Exception.GetType().Name
} finally {
    try {
        $logs = Join-Path $PSScriptRoot 'logs'
        if (-not (Test-Path -LiteralPath $logs -PathType Container)) {
            New-Item -Path $logs -ItemType Directory -Force | Out-Null
        }
        $current = Join-Path $logs 'runs.csv'
        $previous = Join-Path $logs 'runs.previous.csv'
        if ((Test-Path -LiteralPath $current -PathType Leaf) -and
            (Get-Item -LiteralPath $current).Length -gt 1MB) {
            Move-Item -LiteralPath $current -Destination $previous -Force
        }
        [pscustomobject]@{
            at_utc = $startedAt.ToUniversalTime().ToString('o')
            status = $status
            run_id = $runId
            duration_seconds = [math]::Round(((Get-Date) - $startedAt).TotalSeconds, 2)
            error_type = $errorType
        } | Export-Csv -LiteralPath $current -Append -NoTypeInformation -Encoding UTF8
    } catch {
        $code = 1
        $status = 'log_failed'
    }
}
Write-Output ('WORKSTATION_INVENTORY status={0} run_id={1}' -f $status, $runId)
exit $code
