#requires -Version 5.1
<#
.SYNOPSIS
  G2-S1: inventario LOCAL, somente leitura, de uma estacao Windows.
.DESCRIPTION
  Nao instala servicos/tarefas, nao acessa outros hosts, nao envia dados
  pela rede e nao identifica o equipamento para fins de autenticacao.
  Nao coleta usuarios, arquivos, serial de BIOS, MAC nem IP publico.
  Saida: um unico JSON v1 no stdout; trate host/IP como dados internos.
.PARAMETER IncludePrivateIPv4
  Inclui apenas IPs RFC1918 locais (10/8, 172.16/12, 192.168/16).
  Nunca consulta IP externo/publico.
.EXAMPLE
  .\Collect-ItPortalWorkstationSnapshot.ps1 | ConvertFrom-Json
#>
[CmdletBinding()]
param([switch]$IncludePrivateIPv4)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Limit-Text {
    param([object]$Value, [int]$Length = 120)
    if ($null -eq $Value) { return $null }
    $text = ([string]$Value).Trim()
    if (-not $text) { return $null }
    if ($text.Length -gt $Length) { return $text.Substring(0, $Length) }
    return $text
}

function Is-Rfc1918Ipv4 {
    param([string]$Value)
    $address = $null
    if (-not [System.Net.IPAddress]::TryParse($Value, [ref]$address)) { return $false }
    if ($address.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) { return $false }
    $parts = $address.GetAddressBytes()
    return (($parts[0] -eq 10) -or
        ($parts[0] -eq 172 -and $parts[1] -ge 16 -and $parts[1] -le 31) -or
        ($parts[0] -eq 192 -and $parts[1] -eq 168))
}

$hostName = ([Environment]::MachineName).Trim().ToLowerInvariant()
$sections = [ordered]@{
    hardware = 'unavailable'
    os = 'unavailable'
    volumes = 'unavailable'
    network = 'unavailable'
}
$hardware = $null
$osData = $null
$volumes = @()
$privateIpv4 = @()

# Somente WMI/CIM local. Nao consultar arquivos, sessoes ou usuarios.
try {
    $system = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
    $cpu = Get-CimInstance -ClassName Win32_Processor -ErrorAction Stop |
        Select-Object -First 1
    $hardware = [ordered]@{
        manufacturer = Limit-Text $system.Manufacturer 120
        model = Limit-Text $system.Model 120
        cpu_name = if ($null -ne $cpu) { Limit-Text $cpu.Name 160 } else { $null }
        logical_processors = if ($null -ne $system.NumberOfLogicalProcessors) {
            [int]$system.NumberOfLogicalProcessors
        } else { $null }
        memory_total_bytes = if ($null -ne $system.TotalPhysicalMemory) {
            [long]$system.TotalPhysicalMemory
        } else { $null }
    }
    $sections.hardware = 'ok'
} catch {
    # A ausencia da secao nao deve parar a coleta independente das demais.
}

try {
    $winOs = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
    $uptime = $null
    if ($null -ne $winOs.LastBootUpTime) {
        $uptime = [long][Math]::Max(0, (
            [DateTime]::Now - [DateTime]$winOs.LastBootUpTime
        ).TotalSeconds)
    }
    $osData = [ordered]@{
        name = Limit-Text $winOs.Caption 120
        version = Limit-Text $winOs.Version 64
        build_number = Limit-Text $winOs.BuildNumber 40
        architecture = Limit-Text $winOs.OSArchitecture 40
        uptime_seconds = $uptime
    }
    $sections.os = 'ok'
} catch {
    # Coleta parcial e melhor que inventar um sistema operacional.
}

try {
    $disks = @(Get-CimInstance -ClassName Win32_LogicalDisk -Filter 'DriveType=3' -ErrorAction Stop)
    foreach ($disk in @($disks | Select-Object -First 16)) {
        $size = [long]$disk.Size
        $free = [long]$disk.FreeSpace
        if ($size -le 0 -or $free -lt 0 -or $free -gt $size) { continue }
        $volumes += [ordered]@{
            mount_point = ([string]$disk.DeviceID).ToUpperInvariant()
            filesystem = Limit-Text $disk.FileSystem 32
            capacity_bytes = $size
            free_bytes = $free
        }
    }
    $sections.volumes = if ($volumes.Count -gt 0) { 'ok' } else { 'partial' }
} catch {
    # Sem inspecao do conteudo dos discos ou de unidades mapeadas de rede.
}

if ($IncludePrivateIPv4) {
    try {
        $nics = @(Get-CimInstance -ClassName Win32_NetworkAdapterConfiguration -Filter 'IPEnabled=True' -ErrorAction Stop)
        foreach ($nic in @($nics | Select-Object -First 32)) {
            foreach ($ip in @($nic.IPAddress)) {
                if ($ip -and (Is-Rfc1918Ipv4 ([string]$ip))) {
                    $privateIpv4 += [string]$ip
                }
            }
        }
        $privateIpv4 = @($privateIpv4 | Sort-Object -Unique | Select-Object -First 16)
        $sections.network = if ($privateIpv4.Count -gt 0) { 'ok' } else { 'partial' }
    } catch {
        # Nunca consultar servico remoto de IP publico.
    }
}

$states = @($sections.Values)
$status = if (@($states | Where-Object { $_ -eq 'ok' }).Count -eq 4) {
    'complete'
} elseif (@($states | Where-Object { $_ -eq 'unavailable' }).Count -eq 4) {
    'failed'
} else {
    'partial'
}

[ordered]@{
    source = 'windows_workstation_local_v1'
    schema_version = '1'
    run_id = [guid]::NewGuid().ToString()
    observed_at = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
    status = $status
    host = [ordered]@{ hostname = $hostName }
    hardware = $hardware
    os = $osData
    volumes = @($volumes)
    network = [ordered]@{ private_ipv4 = @($privateIpv4) }
    sections_status = $sections
} | ConvertTo-Json -Depth 7 -Compress
