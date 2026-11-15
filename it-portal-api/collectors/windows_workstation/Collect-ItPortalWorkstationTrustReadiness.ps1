#requires -Version 5.1
<#
G2-S4-S2b-P4 | Windows trust readiness (read only).
Reports coarse TPM/Secure Boot capability; NEVER device attestation.
No keys, identifiers, certificates, enrollment, remote access, file writes or network.
The report is local/untrusted and MUST NOT authorize any change.
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function ConvertTo-TriState {
    param($Value)
    if ($null -eq $Value) { return 'unknown' }
    if ($Value -is [bool]) {
        if ($Value) { return 'yes' }
        return 'no'
    }
    return 'unknown'
}

$platform = 'non_windows'
$present = 'unknown'
$ready = 'unknown'
$spec = 'unknown'
$secureBoot = 'unknown'

if ($env:OS -eq 'Windows_NT') {
    $platform = 'windows'
    try {
        $tpm = Get-Tpm -ErrorAction Stop
        if ($null -ne $tpm) {
            $present = ConvertTo-TriState $tpm.TpmPresent
            if ($present -eq 'yes') {
                $ready = ConvertTo-TriState $tpm.TpmReady
            } elseif ($present -eq 'no') {
                $ready = 'no'
            }
        }
    } catch {
        # Missing cmdlet or permissions are UNKNOWN, not ready.
    }

    if ($present -eq 'yes') {
        try {
            $wmiTpm = Get-CimInstance -Namespace 'root\cimv2\security\microsofttpm' -ClassName 'Win32_Tpm' -ErrorAction Stop
            if ($null -ne $wmiTpm) {
                $rawVersion = [string]$wmiTpm.SpecVersion
                if ($rawVersion -match '^\s*2\.0(?:\s*,|$)') {
                    $spec = '2.0'
                } elseif ($rawVersion -match '^\s*1\.2(?:\s*,|$)') {
                    $spec = '1.2'
                }
            }
        } catch {
            # Unavailable WMI or limited permissions remain UNKNOWN.
        }
    }

    try {
        $verifiedBoot = Confirm-SecureBootUEFI -ErrorAction Stop
        if ($verifiedBoot -is [bool]) {
            if ($verifiedBoot) { $secureBoot = 'enabled' }
            else { $secureBoot = 'disabled' }
        }
    } catch {
        # BIOS/non-UEFI, unsupported hardware or no admin privilege => unknown.
    }
}

[ordered]@{
    schema_version = 1
    kind = 'delpi-it-remote-p4-readiness'
    origin = 'unauthenticated-local-readonly'
    collected_at = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    platform = $platform
    tpm = [ordered]@{
        present = $present
        ready = $ready
        spec = $spec
    }
    secure_boot = $secureBoot
    hardware_attested = $false
    key_bound = $false
    activation_authorized = $false
} | ConvertTo-Json -Depth 4 -Compress
