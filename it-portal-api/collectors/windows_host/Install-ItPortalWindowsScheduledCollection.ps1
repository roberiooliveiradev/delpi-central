#requires -Version 5.1
<#
.SYNOPSIS
  Instala coleta horaria do Portal de TI no Windows (instalacao assistida).
.DESCRIPTION
  Rodar interativamente no Windows autorizado com a conta escolhida para a tarefa.
  Copia arquivos revisados para o perfil LOCAL da conta, armazena o segredo
  S2S cifrado com DPAPI e registra tarefa sem guardar o segredo em argumentos.
  A senha da conta Windows e solicitada apenas para o Task Scheduler.
  A tarefa nao e criada se o teste manual DPAPI falhar.
#>
[CmdletBinding()]
param(
    [ValidatePattern('^https://[^\s"]+$')]
    [string]$ApiBaseUrl = 'https://minhadelpi.com.br/apps/it-portal-api',

    [ValidatePattern('^https://[^\s"]+$')]
    [string]$S2sTokenUrl = 'https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/token',

    [ValidatePattern('^[A-Za-z0-9_.-]{3,100}$')]
    [string]$ClientId = 'it-portal-windows-srv-db01',

    [guid]$ServerId = 'e6b46ca6-7b02-449b-b42e-6ddc498f9894',

    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9-]{0,62}$')]
    [string]$ExpectedHostname = 'srv-db01',

    [ValidateRange(30, 1440)]
    [int]$IntervalMinutes = 60,

    [string]$TaskName = 'Delpi-PortalTI-Windows-SRV-DB01'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$localHostname = [Environment]::MachineName.ToLowerInvariant()
if ($localHostname -ne $ExpectedHostname.ToLowerInvariant()) {
    throw ("Hostname incorreto: esperado {0}; host atual {1}." -f $ExpectedHostname, $localHostname)
}
# Novo host deve ter identidade propria, nunca copiar valores do piloto.
if ($localHostname -ne 'srv-db01' -and (
    $ClientId -match 'srv-db01' -or
    $ServerId.ToString() -eq 'e6b46ca6-7b02-449b-b42e-6ddc498f9894' -or
    $TaskName -match 'SRV-DB01'
)) {
    throw 'Configuracao do piloto SRV-DB01 nao pode ser reutilizada em outro servidor.'
}
if (-not $env:LOCALAPPDATA -or $env:LOCALAPPDATA.StartsWith('\\')) {
    throw 'LOCALAPPDATA precisa apontar para uma pasta local do perfil Windows.'
}
Import-Module ScheduledTasks -ErrorAction Stop
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    throw 'Tarefa ja existe. Validar sua configuracao antes de substituir.'
}

$files = @(
    'Collect-ItPortalWindowsInventory.ps1',
    'Send-ItPortalWindowsObservation.ps1',
    'Invoke-ItPortalWindowsScheduledObservation.ps1'
)
foreach ($name in $files) {
    $sourceFile = Join-Path $PSScriptRoot $name
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
        throw "Arquivo obrigatorio nao encontrado no pacote de origem: $name"
    }
    $tokens = $null
    $parseErrors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        $sourceFile, [ref]$tokens, [ref]$parseErrors
    )
    if ($null -ne $parseErrors -and $parseErrors.Count -gt 0) {
        throw "Erro de sintaxe no arquivo aprovado: $name"
    }
}

# G: pode ser uma unidade mapeada e nao existir em tarefas nao interativas.
# Executar sempre a partir do perfil local da conta agendada.
$installDir = Join-Path $env:LOCALAPPDATA 'Delpi\ItPortal'
New-Item -Path $installDir -ItemType Directory -Force | Out-Null
foreach ($name in $files) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $installDir $name) -Force
}

$secretFile = Join-Path $installDir 'client-secret.dpapi'
$secureSecret = Read-Host -Prompt "Client Secret Keycloak de $ClientId (nao aparece)" -AsSecureString
try {
    $encryptedSecret = ConvertFrom-SecureString -SecureString $secureSecret
    [System.IO.File]::WriteAllText($secretFile, $encryptedSecret, [System.Text.Encoding]::ASCII)
} finally {
    $encryptedSecret = $null
    if ($null -ne $secureSecret) { $secureSecret.Dispose() }
}

# Restringe ACL do arquivo a conta atual, SYSTEM e Administradores.
# DPAPI ainda exige a MESMA identidade Windows no MESMO host.
$currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$acl = Get-Acl -LiteralPath $secretFile
$acl.SetAccessRuleProtection($true, $false)
foreach ($rule in @($acl.Access)) {
    [void]$acl.RemoveAccessRuleSpecific($rule)
}
foreach ($sidValue in @(
    $currentIdentity.User.Value,
    'S-1-5-18',
    'S-1-5-32-544'
)) {
    $sid = [Security.Principal.SecurityIdentifier]::new($sidValue)
    $access = [Security.AccessControl.FileSystemAccessRule]::new(
        $sid,
        [Security.AccessControl.FileSystemRights]::FullControl,
        [Security.AccessControl.AccessControlType]::Allow
    )
    [void]$acl.AddAccessRule($access)
}
Set-Acl -LiteralPath $secretFile -AclObject $acl

# Smoke usando o metodo de autenticacao DESASSISTIDO antes de habilitar recorrencia.
$sender = Join-Path $installDir 'Send-ItPortalWindowsObservation.ps1'
$sent = & $sender -ApiBaseUrl $ApiBaseUrl -S2sTokenUrl $S2sTokenUrl `
    -ClientId $ClientId -ServerId $ServerId -ClientSecretDpapiPath $secretFile
if ($null -eq $sent -or $sent.status -ne 'enviado') {
    throw 'Smoke DPAPI falhou. Tarefa NAO registrada.'
}
Write-Output ("SMOKE_DPAPI_OK run_id={0} coleta={1}" -f $sent.run_id, $sent.collected_status)

$runner = Join-Path $installDir 'Invoke-ItPortalWindowsScheduledObservation.ps1'
$exe = Join-Path $PSHOME 'powershell.exe'
$arguments = '-NoLogo -NoProfile -NonInteractive -File "{0}" -ApiBaseUrl "{1}" -S2sTokenUrl "{2}" -ClientId "{3}" -ServerId "{4}" -SecretFile "{5}"' -f `
    $runner, $ApiBaseUrl, $S2sTokenUrl, $ClientId, $ServerId, $secretFile
$action = New-ScheduledTaskAction -Execute $exe -Argument $arguments -WorkingDirectory $installDir
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

$taskPassword = Read-Host -Prompt "Senha WINDOWS de $($currentIdentity.Name) para tarefa mesmo sem sessao aberta" -AsSecureString
$handle = [IntPtr]::Zero
$plainTaskPassword = $null
try {
    $handle = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($taskPassword)
    $plainTaskPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($handle)
    if ([string]::IsNullOrWhiteSpace($plainTaskPassword)) {
        throw 'Senha Windows vazia: tarefa nao registrada.'
    }
    Register-ScheduledTask -TaskName $TaskName -Description 'Portal TI: inventario Windows S2S read-only a cada hora' `
        -Action $action -Trigger $trigger -Settings $settings `
        -User $currentIdentity.Name -Password $plainTaskPassword -RunLevel Limited -ErrorAction Stop | Out-Null
} finally {
    $plainTaskPassword = $null
    if ($handle -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($handle)
    }
    if ($null -ne $taskPassword) { $taskPassword.Dispose() }
}

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
Write-Output ("TAREFA_REGISTRADA: {0}; estado={1}; conta={2}; intervalo={3}min" -f `
    $TaskName, $task.State, $currentIdentity.Name, $IntervalMinutes)
Write-Output ("INSTALADO_EM: {0}" -f $installDir)
Write-Output ("EXECUTAR_TESTE_DA_TAREFA: Start-ScheduledTask -TaskName '{0}'" -f $TaskName)
