#requires -Version 5.1
<#
.SYNOPSIS
  Inventario completo local e read-only dos servicos Windows.
#>
[CmdletBinding()]
param([ValidateRange(1,100)][int]$BatchSize = 100)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$hostName = [Environment]::MachineName.ToLowerInvariant()
$observedAt = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
$runId = [guid]::NewGuid().ToString()
$rawServices = @(Get-CimInstance -ClassName Win32_Service -ErrorAction Stop)
if ($rawServices.Count -eq 0) { throw 'Nenhum servico retornado.' }
if ($rawServices.Count -gt 5000) { throw 'Limite de 5000 servicos excedido.' }
$services = @($rawServices | Sort-Object -Property Name | ForEach-Object {
    $state = ([string]$_.State).Trim().ToLowerInvariant().Replace(' ', '_')
    if ($state -notin @('running','stopped','paused','start_pending','stop_pending','continue_pending','pause_pending')) { $state = 'unknown' }
    $mode = ([string]$_.StartMode).Trim().ToLowerInvariant()
    if ($mode -notin @('auto','manual','disabled','boot','system')) { $mode = 'unknown' }
    $description = if ($null -eq $_.Description) { $null } else { [string]$_.Description }
    if ($description -and $description.Length -gt 500) { $description = $description.Substring(0,500) }
    [ordered]@{
        name = [string]$_.Name
        display_name = [string]$_.DisplayName
        description = $description
        state = $state
        start_mode = $mode
        can_stop = [bool]$_.AcceptStop
    }
})
$count = [int][Math]::Ceiling($services.Count / [double]$BatchSize)
if ($count -gt 50) { throw 'Limite de 50 lotes excedido.' }
for ($index = 0; $index -lt $count; $index++) {
    $first = $index * $BatchSize
    $last = [Math]::Min($first + $BatchSize - 1, $services.Count - 1)
    [ordered]@{
        run_id = $runId
        schema_version = '1'
        observed_at = $observedAt
        host_identity = @{ hostname = $hostName }
        batch_index = $index
        batch_count = $count
        services = @($services[$first..$last])
    } | ConvertTo-Json -Compress -Depth 5
}
