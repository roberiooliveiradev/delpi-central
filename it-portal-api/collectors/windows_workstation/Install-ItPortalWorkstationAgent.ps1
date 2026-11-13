#requires -Version 5.1
<#
.SYNOPSIS
 G2-S3: instala coletor Windows com tarefa DESABILITADA, ou mostra plano.
.DESCRIPTION
 Sem -Activate: somente plano; sem modificacoes. Com -Activate: exige
 scripts assinados, host correto, Keycloak S2S funcional e DPAPI CurrentUser.
 Tarefa usa logon INTERATIVO (sem armazenar senha Windows), nao funciona
 apos a conta sair do Windows. Nunca instala acesso remoto.
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https://[A-Za-z0-9.-]+(?::[0-9]{1,5})?(?:/[A-Za-z0-9%/._-]*)?$')]
    [string]$ApiBaseUrl,
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https://[A-Za-z0-9.-]+(?::[0-9]{1,5})?(?:/[A-Za-z0-9%/._-]*)?$')]
    [string]$S2sTokenUrl,
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9_.-]{3,100}$')]
    [string]$ClientId,
    [Parameter(Mandatory = $true)]
    [guid]$WorkstationId,
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9.-]{0,252}$')]
    [string]$ExpectedHostname,
    [ValidateRange(30, 1440)]
    [int]$IntervalMinutes = 60,
    [ValidatePattern('^[A-Fa-f0-9]{40}$')]
    [string]$TrustedSignerThumbprint = '',
    [switch]$IncludePrivateIPv4,
    [switch]$Activate
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($WorkstationId -eq [guid]::Empty) { throw 'WorkstationIdObrigatorio' }

$taskName = 'Delpi-PortalTI-WorkstationInventory-' + $WorkstationId.ToString('N')
$files = @(
    'Collect-ItPortalWorkstationSnapshot.ps1',
    'Send-ItPortalWorkstationSnapshot.ps1',
    'Invoke-ItPortalWorkstationScheduledSnapshot.ps1'
)
Write-Output ('G2_S3_PLAN workstation={0} task={1} interval={2}min' -f $WorkstationId, $taskName, $IntervalMinutes)
Write-Output 'G2_S3_PLAN_ONLY: sem -Activate nenhum arquivo, segredo ou tarefa e alterado.'
Write-Output 'GATES: Windows piloto, Keycloak individual, binding S2S, assinatura corporativa, aceite.'
if (-not $Activate) { return }

if (-not $TrustedSignerThumbprint) { throw 'TrustedSignerRequired' }
if ($PSVersionTable.PSEdition -ne 'Desktop') { throw 'WindowsPowerShell51Required' }
$actualHost = [Environment]::MachineName.Trim().ToLowerInvariant()
if ($actualHost -ne $ExpectedHostname.Trim().ToLowerInvariant()) {
    throw 'HostnameMismatch'
}
if (-not $env:LOCALAPPDATA -or
    -not [IO.Path]::IsPathRooted($env:LOCALAPPDATA) -or
    $env:LOCALAPPDATA.StartsWith('\\') -or $env:LOCALAPPDATA.Contains('"')) {
    throw 'LocalAppDataInvalid'
}
$installDir = Join-Path $env:LOCALAPPDATA ('Delpi\PortalTI\Workstations\{0}' -f $WorkstationId.ToString('N'))
if ($installDir.Contains('"') -or $installDir.Contains([char]10)) {
    throw 'InstallPathInvalid'
}

function Assert-Signed {
    param([string]$FilePath, [string]$Thumbprint)
    if (-not (Test-Path -LiteralPath $FilePath -PathType Leaf)) {
        throw 'PackageFileMissing'
    }
    $tokens = $null
    $parseErrors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        $FilePath, [ref]$tokens, [ref]$parseErrors
    )
    if ($null -ne $parseErrors -and $parseErrors.Count -gt 0) {
        throw 'InvalidPowerShellSyntax'
    }
    $signature = Get-AuthenticodeSignature -FilePath $FilePath -ErrorAction Stop
    if ($signature.Status -ne 'Valid' -or
        $null -eq $signature.SignerCertificate -or
        $signature.SignerCertificate.Thumbprint.ToUpperInvariant() -ne $Thumbprint) {
        throw 'UntrustedCodeSignature'
    }
}

Import-Module ScheduledTasks -ErrorAction Stop
if ((Test-Path -LiteralPath $installDir) -or
    (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue)) {
    throw 'ExistingInstallationRequiresManualReview'
}
$signer = $TrustedSignerThumbprint.ToUpperInvariant()
Assert-Signed -FilePath $PSCommandPath -Thumbprint $signer
foreach ($file in $files) {
    Assert-Signed -FilePath (Join-Path $PSScriptRoot $file) -Thumbprint $signer
}

if (-not $PSCmdlet.ShouldProcess($taskName, 'Instalar pacote assinado e registrar tarefa DESABILITADA')) {
    return
}
$created = $false
$taskCreated = $false
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    New-Item -Path $installDir -ItemType Directory -ErrorAction Stop | Out-Null
    $created = $true

    # ACL exclusiva da conta que executara a tarefa + SYSTEM + Administradores.
    $acl = Get-Acl -LiteralPath $installDir
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($rule in @($acl.Access)) {
        [void]$acl.RemoveAccessRuleSpecific($rule)
    }
    foreach ($sidValue in @($identity.User.Value, 'S-1-5-18', 'S-1-5-32-544')) {
        $sid = [Security.Principal.SecurityIdentifier]::new($sidValue)
        $rule = [Security.AccessControl.FileSystemAccessRule]::new(
            $sid,
            [Security.AccessControl.FileSystemRights]::FullControl,
            [Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit',
            [Security.AccessControl.PropagationFlags]::None,
            [Security.AccessControl.AccessControlType]::Allow
        )
        [void]$acl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $installDir -AclObject $acl -ErrorAction Stop

    foreach ($file in $files) {
        $dest = Join-Path $installDir $file
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $file) -Destination $dest -ErrorAction Stop
        Assert-Signed -FilePath $dest -Thumbprint $signer
    }

    $settings = [ordered]@{
        schema_version = 1
        workstation_id = $WorkstationId.ToString()
        expected_hostname = $actualHost
        api_base_url = $ApiBaseUrl.TrimEnd('/')
        s2s_token_url = $S2sTokenUrl
        client_id = $ClientId
        include_private_ipv4 = [bool]$IncludePrivateIPv4
        trusted_signer_thumbprint = $signer
        task_name = $taskName
    }
    [IO.File]::WriteAllText(
        (Join-Path $installDir 'settings.json'),
        ($settings | ConvertTo-Json -Depth 4),
        [Text.UTF8Encoding]::new($false)
    )

    $secretPath = Join-Path $installDir 'client-secret.dpapi'
    $secret = Read-Host -Prompt 'Client Secret Keycloak INDIVIDUAL (oculto)' -AsSecureString
    try {
        $ciphertext = ConvertFrom-SecureString -SecureString $secret
        [IO.File]::WriteAllText($secretPath, $ciphertext, [Text.Encoding]::ASCII)
    } finally {
        $ciphertext = $null
        if ($null -ne $secret) { $secret.Dispose() }
    }

    $args = @{
        ApiBaseUrl = $settings.api_base_url
        S2sTokenUrl = $settings.s2s_token_url
        ClientId = $ClientId
        WorkstationId = $WorkstationId
        ClientSecretDpapiPath = $secretPath
        IncludePrivateIPv4 = [bool]$IncludePrivateIPv4
    }
    $smoke = & (Join-Path $installDir 'Send-ItPortalWorkstationSnapshot.ps1') @args
    if ($null -eq $smoke -or $smoke.status -ne 'enviado' -or
        [string]$smoke.workstation_id -ne $WorkstationId.ToString()) {
        throw 'SmokeFailed'
    }

    $runner = Join-Path $installDir 'Invoke-ItPortalWorkstationScheduledSnapshot.ps1'
    $action = New-ScheduledTaskAction -Execute (Join-Path $PSHOME 'powershell.exe') -Argument ('-NoLogo -NoProfile -NonInteractive -File "{0}"' -f $runner) -WorkingDirectory $installDir
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 3650)
    $taskSettings = New-ScheduledTaskSettingsSet -Disable -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 4)
    $principal = New-ScheduledTaskPrincipal -UserId $identity.User.Value -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $taskSettings -Principal $principal -Description 'Portal TI: inventario Windows sem controle remoto' -ErrorAction Stop | Out-Null
    $taskCreated = $true
    if ((Get-ScheduledTask -TaskName $taskName -ErrorAction Stop).State -ne 'Disabled') {
        throw 'TaskWasNotDisabled'
    }
    Write-Output ('G2_S3_INSTALLED_DISABLED task={0}' -f $taskName)
    Write-Output 'G2_S3_NEXT: habilitar separadamente apos homologacao do piloto.'
} catch {
    if ($taskCreated) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    }
    if ($created) {
        Remove-Item -LiteralPath $installDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    # Nao propagar corpo HTTP ou respostas possivelmente contendo token.
    throw 'G2_S3_INSTALL_ABORTED: pre-requisito falhou; tarefa nao ativada.'
}
