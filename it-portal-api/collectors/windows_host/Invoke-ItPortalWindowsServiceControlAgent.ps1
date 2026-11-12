#requires -Version 5.1
<#
.SYNOPSIS
  Agente de controle Windows com conexao apenas de saida HTTPS.
.DESCRIPTION
  Consulta fila a cada 2 segundos. Nao executa comandos genericos, apenas
  Start/Stop/Restart via ServiceController em nomes exatos autorizados.
  Nao altera dependencias, configuracoes ou privilegios de servicos.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^https://[^\s"]+$')][string]$ApiBaseUrl,
    [Parameter(Mandatory=$true)][ValidatePattern('^https://[^\s"]+$')][string]$S2sTokenUrl,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_.-]{3,100}$')][string]$ClientId,
    [Parameter(Mandatory=$true)][guid]$ServerId,
    [Parameter(Mandatory=$true)][string]$SecretFile,
    [Parameter(Mandatory=$true)][string]$AllowedServices
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

if ([Environment]::MachineName.ToLowerInvariant() -ne 'srv-db01') {
    throw 'Piloto do controle remoto autorizado apenas em SRV-DB01.'
}
if (-not [IO.Path]::IsPathRooted($SecretFile) -or -not (Test-Path -LiteralPath $SecretFile -PathType Leaf)) {
    throw 'Credencial DPAPI indisponivel.'
}
$protected = @('rpcss','dcomlaunch','eventlog','plugplay','schedule','winmgmt','samss','lsass','power','profsvc','bfe','mpssvc','lanmanserver','netlogon','wuauserv','cryptsvc')
$allow = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($name in $AllowedServices.Split(',')) {
    $trimmed = $name.Trim()
    if (-not $trimmed) { continue }
    if ($trimmed -notmatch '^[a-zA-Z0-9_.$-]{1,200}$' -or $protected -contains $trimmed.ToLowerInvariant()) {
        throw 'Allowlist local invalida ou contem servico protegido.'
    }
    [void]$allow.Add($trimmed)
}
if ($allow.Count -lt 1) { throw 'Nenhum servico local autorizado.' }

$pollUrl = '{0}/collector/v1/servers/{1}/host-services/control/next?hostname={2}' -f $ApiBaseUrl.TrimEnd('/'),$ServerId,[uri]::EscapeDataString([Environment]::MachineName.ToLowerInvariant())
$reportPrefix = '{0}/collector/v1/servers/{1}/host-services/control' -f $ApiBaseUrl.TrimEnd('/'),$ServerId
$lastTokenTime = [datetime]::MinValue
$accessToken = $null
$failures = 0

function Get-ControlToken {
    $encrypted = (Get-Content -LiteralPath $SecretFile -Raw -ErrorAction Stop).Trim()
    $secure = ConvertTo-SecureString -String $encrypted -ErrorAction Stop
    $encrypted = $null
    $ptr = [IntPtr]::Zero
    try {
        $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
        $response = Invoke-RestMethod -Uri $S2sTokenUrl -Method Post -TimeoutSec 15 -ContentType 'application/x-www-form-urlencoded' -Body @{grant_type='client_credentials';client_id=$ClientId;client_secret=$plain} -ErrorAction Stop
        if (-not $response.access_token) { throw 'Token ausente.' }
        return [string]$response.access_token
    } finally {
        $plain = $null
        if ($ptr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
        if ($null -ne $secure) { $secure.Dispose() }
    }
}

function Get-ExactService([string]$name) {
    $svc = [System.ServiceProcess.ServiceController]::new($name)
    $svc.Refresh()
    if (-not [string]::Equals($svc.ServiceName,$name,[StringComparison]::OrdinalIgnoreCase)) {
        $svc.Dispose()
        throw 'Identidade inconsistente.'
    }
    return $svc
}

function Get-ServiceState($svc) {
    $svc.Refresh()
    switch ($svc.Status.ToString()) {
        'Running' { return 'running' }
        'Stopped' { return 'stopped' }
        'Paused' { return 'paused' }
        default { return 'unknown' }
    }
}

function Invoke-ApprovedAction($job) {
    $result = @{status='failed';state_after=$null;error_code='execution_failed'}
    if (-not $job -or $job.action -notin @('start','stop','restart') -or [string]$job.service_name -notmatch '^[a-zA-Z0-9_.$-]{1,200}$' -or -not $allow.Contains([string]$job.service_name)) {
        $result.error_code = 'not_allowed'
        return $result
    }
    $svc = $null
    try {
        $svc = Get-ExactService -name ([string]$job.service_name)
        $before = Get-ServiceState $svc
        if ($before -ne [string]$job.state_before) {
            $result.error_code = 'precondition_failed'
            $result.state_after = $before
            return $result
        }
        if ($job.action -eq 'start') {
            if ($before -ne 'stopped') { $result.error_code='precondition_failed';return $result }
            $cim = Get-CimInstance Win32_Service -ErrorAction Stop | Where-Object { $_.Name -eq $job.service_name } | Select-Object -First 1
            if ($null -eq $cim -or $cim.StartMode -eq 'Disabled') {
                $result.error_code = 'disabled';return $result
            }
            $svc.Start()
            $svc.WaitForStatus([System.ServiceProcess.ServiceControllerStatus]::Running,[TimeSpan]::FromSeconds(25))
        } else {
            if ($before -ne 'running') { $result.error_code='precondition_failed';return $result }
            if (-not $svc.CanStop) { $result.error_code='not_allowed';return $result }
            if (@($svc.DependentServices | Where-Object { $_.Status -eq [System.ServiceProcess.ServiceControllerStatus]::Running }).Count -gt 0) {
                $result.error_code = 'dependent_services';return $result
            }
            $svc.Stop()
            $svc.WaitForStatus([System.ServiceProcess.ServiceControllerStatus]::Stopped,[TimeSpan]::FromSeconds(25))
            if ($job.action -eq 'restart') {
                $svc.Start()
                $svc.WaitForStatus([System.ServiceProcess.ServiceControllerStatus]::Running,[TimeSpan]::FromSeconds(25))
            }
        }
        $after = Get-ServiceState $svc
        $expected = if ($job.action -eq 'stop') { 'stopped' } else { 'running' }
        $result.state_after = $after
        if ($after -eq $expected) {
            $result.status = 'succeeded'
            $result.error_code = $null
        } else {
            $result.error_code = 'precondition_failed'
        }
        return $result
    } catch [System.InvalidOperationException] {
        $result.error_code = 'service_not_found'
        return $result
    } catch [System.TimeoutException] {
        $result.error_code = 'timeout'
        return $result
    } catch [System.UnauthorizedAccessException] {
        $result.error_code = 'access_denied'
        return $result
    } catch {
        $result.error_code = 'execution_failed'
        return $result
    } finally {
        if ($null -ne $svc) { $svc.Dispose() }
    }
}

function Write-SafeLog([string]$state,[string]$id,[string]$result) {
    $folder = Join-Path $PSScriptRoot 'logs'
    if (-not (Test-Path -LiteralPath $folder -PathType Container)) {
        New-Item -ItemType Directory -Force -Path $folder | Out-Null
    }
    $file = Join-Path $folder 'agent.csv'
    if ((Test-Path -LiteralPath $file -PathType Leaf) -and (Get-Item -LiteralPath $file).Length -gt 1MB) {
        Move-Item -LiteralPath $file -Destination (Join-Path $folder 'agent.previous.csv') -Force
    }
    [pscustomobject]@{at=(Get-Date).ToString('o');event=$state;id=$id;result=$result} | Export-Csv -LiteralPath $file -NoTypeInformation -Append -Encoding UTF8
}

while ($true) {
    try {
        if (-not $accessToken -or ((Get-Date)-$lastTokenTime).TotalSeconds -ge 180) {
            $accessToken = Get-ControlToken
            $lastTokenTime = Get-Date
        }
        $headers = @{'X-Delpi-Service-Authorization'="Bearer $accessToken"}
        $response = Invoke-RestMethod -Uri $pollUrl -Method Get -Headers $headers -TimeoutSec 15
        $failures = 0
        if ($null -ne $response.data) {
            $job = $response.data
            $work = Invoke-ApprovedAction $job
            $reportUrl = '{0}/{1}/result' -f $reportPrefix,[uri]::EscapeDataString([string]$job.id)
            $payload = @{lease=[string]$job.lease;status=[string]$work.status;state_after=$work.state_after;error_code=$work.error_code} | ConvertTo-Json -Compress
            $reported = $false
            for ($attempt = 0; $attempt -lt 2; $attempt++) {
                try {
                    $confirmation = Invoke-RestMethod -Uri $reportUrl -Method Post -Headers $headers -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($payload)) -TimeoutSec 15
                    if ($confirmation.data.id -ne [string]$job.id) { throw 'Resposta inesperada.' }
                    $reported = $true
                    break
                } catch { Start-Sleep -Seconds 1 }
            }
            $outcome = if ($reported) { $work.status } else { 'unconfirmed' }
            Write-SafeLog 'action' ([string]$job.id) $outcome
        }
        Start-Sleep -Seconds 2
    } catch {
        $accessToken = $null
        $failures++
        Write-SafeLog 'poll_error' '' 'unavailable'
        if ($failures -ge 10) { throw 'Agente indisponivel: encerrando sem executar comandos.' }
        Start-Sleep -Seconds ([math]::Min(30,2*$failures))
    }
}
