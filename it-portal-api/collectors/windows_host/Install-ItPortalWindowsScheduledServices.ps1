#requires -Version 5.1
<#
.SYNOPSIS
  Instala a coleta Windows SCM do SRV-DB01 a cada 5 minutos.
.DESCRIPTION
  Instalacao assistida, separada da tarefa Windows E4.S4. Executar na mesma
  conta Windows nao administrativa destinada a executar o agendamento.
  Protege Client Secret Keycloak em DPAPI do usuario, executa smoke real
  antes de registrar tarefa e nao persiste credenciais em argumentos/logs.
#>
[CmdletBinding()]
param(
    [ValidatePattern('^https://[^\s"]+$')]
    [string]$ApiBaseUrl = 'https://minhadelpi.com.br/apps/it-portal-api',

    [ValidatePattern('^https://[^\s"]+$')]
    [string]$S2sTokenUrl = 'https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/token',

    [ValidatePattern('^[A-Za-z0-9_.-]{3,100}$')]
    [string]$ClientId = 'it-portal-windows-services-srv-db01',

    [guid]$ServerId = 'e6b46ca6-7b02-449b-b42e-6ddc498f9894',

    [ValidateRange(5,1440)]
    [int]$IntervalMinutes = 5,

    [ValidatePattern('^[A-Za-z0-9_.-]{5,120}$')]
    [string]$TaskName = 'Delpi-PortalTI-WindowsServices-SRV-DB01'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([Environment]::MachineName.ToLowerInvariant() -ne 'srv-db01') {
    throw 'Instalacao bloqueada: destino deve ser SRV-DB01.'
}
if (-not $env:LOCALAPPDATA -or -not [IO.Path]::IsPathRooted($env:LOCALAPPDATA) -or
    $env:LOCALAPPDATA.StartsWith('\\')) {
    throw 'LOCALAPPDATA deve ser um caminho local do perfil Windows.'
}
Import-Module ScheduledTasks -ErrorAction Stop
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    throw 'Tarefa ja existe. Inspecionar antes de qualquer substituicao.'
}

# A tarefa nao depende do G:, que pode ser uma unidade mapeada de sessao.
$files = @(
    'Collect-ItPortalWindowsServices.ps1',
    'Send-ItPortalWindowsServices.ps1',
    'Invoke-ItPortalWindowsScheduledServices.ps1'
)
foreach ($name in $files) {
    $source = Join-Path $PSScriptRoot $name
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Arquivo obrigatorio ausente: $name"
    }
    $tokens = $null
    $parseErrors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        $source, [ref]$tokens, [ref]$parseErrors
    )
    if ($null -ne $parseErrors -and $parseErrors.Count -gt 0) {
        throw "Script com erro de sintaxe: $name"
    }
}

$installDir = Join-Path $env:LOCALAPPDATA 'Delpi\ItPortal\WindowsServices'
if ($installDir.Contains('"')) { throw 'Caminho local invalido.' }
New-Item -Path $installDir -ItemType Directory -Force | Out-Null
foreach ($name in $files) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $installDir $name) -Force
}

$currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$secretFile = Join-Path $installDir 'client-secret.dpapi'
if (Test-Path -LiteralPath $secretFile -PathType Leaf) {
    throw 'Segredo DPAPI ja existe; revisar instalacao anterior antes de substituir.'
}
$secureSecret = Read-Host -Prompt "Client Secret Keycloak de $ClientId (oculto)" -AsSecureString
try {
    $encryptedSecret = ConvertFrom-SecureString -SecureString $secureSecret
    [IO.File]::WriteAllText($secretFile, $encryptedSecret, [Text.Encoding]::ASCII)
} finally {
    $encryptedSecret = $null
    if ($null -ne $secureSecret) { $secureSecret.Dispose() }
}

# Acesso exclusivo ao dono da tarefa, SYSTEM e Administradores.
$acl = Get-Acl -LiteralPath $secretFile
$acl.SetAccessRuleProtection($true, $false)
foreach ($rule in @($acl.Access)) {
    [void]$acl.RemoveAccessRuleSpecific($rule)
}
foreach ($sidValue in @($currentIdentity.User.Value, 'S-1-5-18', 'S-1-5-32-544')) {
    $sid = [Security.Principal.SecurityIdentifier]::new($sidValue)
    $rule = [Security.AccessControl.FileSystemAccessRule]::new(
        $sid,
        [Security.AccessControl.FileSystemRights]::FullControl,
        [Security.AccessControl.AccessControlType]::Allow
    )
    [void]$acl.AddAccessRule($rule)
}
Set-Acl -LiteralPath $secretFile -AclObject $acl

# So registra apos comprovar descriptografia DPAPI + envio com o novo cliente.
$sender = Join-Path $installDir 'Send-ItPortalWindowsServices.ps1'
try {
    $smoke = & $sender -ApiBaseUrl $ApiBaseUrl -S2sTokenUrl $S2sTokenUrl -ClientId $ClientId -ServerId $ServerId -ClientSecretDpapiPath $secretFile
    if ($null -eq $smoke -or $smoke.status -ne 'enviado') {
        throw 'SmokeReadOnlyFailed'
    }
} catch {
    Remove-Item -LiteralPath $secretFile -Force -ErrorAction SilentlyContinue
    throw 'SMOKE_DPAPI_FALHOU: tarefa nao registrada. Verificar credenciais/escopo/ligacao com API.'
}
Write-Output ("SMOKE_DPAPI_OK run_id={0} lotes={1}" -f $smoke.run_id, $smoke.batches)

$runner = Join-Path $installDir 'Invoke-ItPortalWindowsScheduledServices.ps1'
$exe = Join-Path $PSHOME 'powershell.exe'
$arguments = '-NoLogo -NoProfile -NonInteractive -File "{0}" -ApiBaseUrl "{1}" -S2sTokenUrl "{2}" -ClientId "{3}" -ServerId "{4}" -SecretFile "{5}"' -f $runner, $ApiBaseUrl, $S2sTokenUrl, $ClientId, $ServerId, $secretFile
$action = New-ScheduledTaskAction -Execute $exe -Argument $arguments -WorkingDirectory $installDir
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 4)

# A conta agendada e a mesma que cifrou o segredo; requer Log on as batch job.
$taskPassword = Read-Host -Prompt "Senha WINDOWS de $($currentIdentity.Name) para executar sem sessao conectada" -AsSecureString
$handle = [IntPtr]::Zero
$plainPassword = $null
try {
    $handle = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($taskPassword)
    $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($handle)
    if ([string]::IsNullOrWhiteSpace($plainPassword)) {
        throw 'Senha Windows vazia. Tarefa nao registrada.'
    }
    Register-ScheduledTask -TaskName $TaskName -Description 'Portal TI: inventario SCM Windows read-only, a cada 5 minutos' -Action $action -Trigger $trigger -Settings $settings -User $currentIdentity.Name -Password $plainPassword -RunLevel Limited -ErrorAction Stop | Out-Null
} finally {
    $plainPassword = $null
    if ($handle -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($handle)
    }
    if ($null -ne $taskPassword) { $taskPassword.Dispose() }
}

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
Write-Output ("TAREFA_REGISTRADA: {0}; estado={1}; conta={2}; intervalo={3}min" -f $TaskName, $task.State, $currentIdentity.Name, $IntervalMinutes)
Write-Output ("INSTALADO_EM: {0}" -f $installDir)
Write-Output ("EXECUTAR_TESTE: Start-ScheduledTask -TaskName '{0}'" -f $TaskName)
