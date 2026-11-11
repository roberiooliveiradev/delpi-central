#requires -Version 5.1
<#
.SYNOPSIS
  Snapshot local, somente leitura, de um Windows Server para o Portal de TI.
.DESCRIPTION
  Não instala agente, não usa WinRM, não faz descoberta de rede e NÃO envia
  dados à API. O JSON emitido no stdout é um diagnóstico a revisar antes
  de cadastrar/autorizar cada servidor. Não execute em estações de trabalho.
.EXAMPLE
  .\Collect-ItPortalWindowsInventory.ps1 -ServiceNames 'EventLog','W32Time','MSSQLSERVER'
#>
[CmdletBinding()]
param(
    [string[]]$ServiceNames = @('EventLog', 'W32Time', 'LanmanServer')
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$hostname = [Environment]::MachineName.ToLowerInvariant()
$summary = [ordered]@{
    identity = [ordered]@{ hostname = $hostname; machine_id = $null }
    os = $null
    virtualization = $null
    cpu_logical = $null
    cpu_usage_percent = $null
    uptime_seconds = $null
    memory = $null
    volumes = @()
    host_nics = @()
    windows_services = @()
}
$sections = [ordered]@{
    identity = 'ok'
    os = 'unavailable'
    cpu = 'unavailable'
    memory = 'unavailable'
    volumes = 'unavailable'
    nics = 'unavailable'
    windows_services = 'unavailable'
}

# UUID de hardware em hash SHA-256. Nunca transmitir UUID/serial bruto.
try {
    $uuid = [string](Get-CimInstance -ClassName Win32_ComputerSystemProduct -ErrorAction Stop).UUID
    if ($uuid -and $uuid -match '^[0-9a-fA-F-]{36}$' -and
        $uuid -notmatch '^(00000000|FFFFFFFF)-') {
        $sha = [Security.Cryptography.SHA256]::Create()
        try {
            $bytes = [Text.Encoding]::UTF8.GetBytes($uuid.Trim().ToLowerInvariant())
            $summary.identity.machine_id = [BitConverter]::ToString(
                $sha.ComputeHash($bytes)
            ).Replace('-', '').ToLowerInvariant()
        } finally {
            $sha.Dispose()
        }
    }
} catch {
    # Identidade por hostname continua disponível; revisão manual obrigatória.
}

try {
    $winOs = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
    $computer = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
    $summary.os = [ordered]@{
        name = [string]$winOs.Caption
        version = [string]$winOs.Version
        pretty_name = [string]$winOs.Caption
        kernel = $null
        architecture = [string]$winOs.OSArchitecture
    }
    $summary.virtualization = [ordered]@{
        type = $null
        hardware_model = [string]$computer.Model
        vendor = [string]$computer.Manufacturer
    }
    $summary.cpu_logical = [int]$computer.NumberOfLogicalProcessors
    if ($winOs.LastBootUpTime) {
        $summary.uptime_seconds = [long][Math]::Max(
            0, ([DateTime]::Now - [DateTime]$winOs.LastBootUpTime).TotalSeconds
        )
    }
    $sections.os = 'ok'
    $summary.memory = [ordered]@{
        total_bytes = [long]$winOs.TotalVisibleMemorySize * 1024
        available_bytes = [long]$winOs.FreePhysicalMemory * 1024
    }
    $sections.memory = 'ok'
} catch {
    # CIM indisponível não impede a coleta das demais seções.
}

try {
    $processors = @(Get-CimInstance -ClassName Win32_Processor -ErrorAction Stop)
    $loads = @($processors | Where-Object { $null -ne $_.LoadPercentage } |
        ForEach-Object { [double]$_.LoadPercentage })
    if ($loads.Count -gt 0) {
        $summary.cpu_usage_percent = [Math]::Round(
            [double](($loads | Measure-Object -Average).Average), 2
        )
        $sections.cpu = 'ok'
    }
} catch {
    # Métrica pontual de CPU indisponível.
}

try {
    $volumes = @(Get-CimInstance -ClassName Win32_LogicalDisk -Filter 'DriveType=3' -ErrorAction Stop |
        Select-Object -First 32 | ForEach-Object {
            $size = [long]$_.Size
            $free = [long]$_.FreeSpace
            if ($size -gt 0) {
                [ordered]@{
                    mount_point = [string]$_.DeviceID
                    filesystem = [string]$_.FileSystem
                    size_bytes = $size
                    used_bytes = $size - $free
                    available_bytes = $free
                    used_percent = [Math]::Round(100 * ($size - $free) / $size, 2)
                }
            }
        })
    $summary.volumes = $volumes
    $sections.volumes = if ($volumes.Count -gt 0) { 'ok' } else { 'partial' }
} catch {
    # Não inspecionar discos de rede nem shares.
}

try {
    $nics = @(Get-CimInstance -ClassName Win32_NetworkAdapterConfiguration -Filter 'IPEnabled=True' -ErrorAction Stop |
        Select-Object -First 32 | ForEach-Object {
            [ordered]@{
                name = ([string]$_.Description).Substring(0, [Math]::Min(40, ([string]$_.Description).Length))
                addresses = @($_.IPAddress | Where-Object { $_ } | Select-Object -First 8)
                state = 'up'
            }
        })
    $summary.host_nics = $nics
    $sections.nics = if ($nics.Count -gt 0) { 'ok' } else { 'partial' }
} catch {
    # Nenhuma varredura de IP; apenas interfaces do host local.
}

$validServiceNames = @($ServiceNames | Where-Object {
    $_ -is [string] -and $_ -match '^[A-Za-z0-9_.-]{1,100}$'
} | Select-Object -Unique -First 40)
try {
    $services = @($validServiceNames | ForEach-Object {
        $name = $_
        try {
            $service = Get-Service -Name $name -ErrorAction Stop
            [ordered]@{
                name = $name
                active_state = $service.Status.ToString().ToLowerInvariant()
                sub_state = $service.StartType.ToString().ToLowerInvariant()
                unit_file_state = $null
            }
        } catch {
            [ordered]@{
                name = $name
                active_state = 'not_found'
                sub_state = $null
                unit_file_state = $null
            }
        }
    })
    $summary.windows_services = $services
    $sections.windows_services = if ($validServiceNames.Count -gt 0) { 'ok' } else { 'partial' }
} catch {
    # A observação parcial é preferível à interrupção da coleta.
}

$values = @($sections.Values)
$overall = if (@($values | Where-Object { $_ -ne 'ok' }).Count -eq 0) {
    'complete'
} elseif (@($values | Where-Object { $_ -eq 'ok' }).Count -eq 0) {
    'failed'
} else {
    'partial'
}

[ordered]@{
    run_id = [guid]::NewGuid().ToString()
    source = 'windows_host_collector'
    schema_version = '1'
    status = $overall
    observed_at = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
    host_identity = [ordered]@{
        hostname = $hostname
        machine_id = $summary.identity.machine_id
    }
    summary = $summary
    sections_status = $sections
} | ConvertTo-Json -Depth 9 -Compress
