#requires -Version 5.1
<#
.SYNOPSIS
  Provisao assistida do agente piloto Windows do #1585.
.DESCRIPTION
  So apos revisao do PR, CI verde, allowlists BFF/Windows, Keycloak
  e autorizacao da operacao. Nao altera coletor SCM existente.
#>
[CmdletBinding()]
param(
    [ValidatePattern('^https://[^\s"]+$')]
    [string]$ApiBaseUrl = 'https://minhadelpi.com.br/apps/it-portal-api',
    [ValidatePattern('^https://[^\s"]+$')]
    [string]$S2sTokenUrl = 'https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/token',
    [ValidatePattern('^[A-Za-z0-9_.-]{3,100}$')]
    [string]$ClientId = 'it-portal-windows-control-srv-db01',
    [guid]$ServerId = 'e6b46ca6-7b02-449b-b42e-6ddc498f9894',
    [Parameter(Mandatory=$true)][string]$ApprovedServiceNames,
    [switch]$Activate
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

if ([Environment]::MachineName.ToLowerInvariant() -ne 'srv-db01') {
    throw 'Instalacao permitida somente no servidor piloto SRV-DB01.'
}
$taskName = 'Delpi-PortalTI-WindowsControl-SRV-DB01'
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    throw 'Agente ja instalado: nao sobrescrever tarefa sem procedimento de alteracao.'
}
if (-not $env:LOCALAPPDATA -or -not [IO.Path]::IsPathRooted($env:LOCALAPPDATA) -or $env:LOCALAPPDATA.StartsWith('\')) {
    throw 'Perfil Windows local obrigatorio para DPAPI.'
}
$protected = @('rpcss','dcomlaunch','eventlog','plugplay','schedule','winmgmt','samss','lsass','power','profsvc','bfe','mpssvc','lanmanserver','netlogon','wuauserv','cryptsvc')
$names = @($ApprovedServiceNames.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($names.Count -eq 0 -or $names.Count -gt 5) {
    throw 'Piloto: informe de 1 a 5 nomes tecnicos de servicos aprovados.'
}
foreach ($n in $names) {
    if ($n -notmatch '^[a-zA-Z0-9_.$-]{1,200}$' -or $protected -contains $n.ToLowerInvariant()) {
        throw 'Nome tecnico invalido ou servico Windows protegido.'
    }
    if ($null -eq (Get-Service -Name $n -ErrorAction SilentlyContinue | Where-Object { $_.Name -ieq $n })) {
        throw 'Servico aprovado nao localizado no Windows.'
    }
}
$source = Join-Path $PSScriptRoot 'Invoke-ItPortalWindowsServiceControlAgent.ps1'
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw 'Script do agente ausente; copie apenas arquivo revisado do PR.'
}
$tokens = $null
$errors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($source,[ref]$tokens,[ref]$errors)
if ($null -ne $errors -and $errors.Count -gt 0) {
    throw 'Arquivo do agente contem erro de sintaxe.'
}
$installDir = Join-Path $env:LOCALAPPDATA 'Delpi\ItPortal\WindowsControl'
if ($installDir.Contains('"')) { throw 'Caminho invalido.' }
if (-not $Activate) {
    Write-Output ('PREPARADO: instalar para conta ' + [Security.Principal.WindowsIdentity]::GetCurrent().Name)
    Write-Output ('Servicos liberaveis: ' + ($names -join ', '))
    Write-Output ('Destino previsto: ' + $installDir)
    Write-Output 'Nenhuma alteracao realizada. Revise em janela autorizada e repita com -Activate.'
    return
}
New-Item -Path $installDir -ItemType Directory -Force | Out-Null
$runner = Join-Path $installDir 'Invoke-ItPortalWindowsServiceControlAgent.ps1'
Copy-Item -LiteralPath $source -Destination $runner -Force
$secretFile = Join-Path $installDir 'client-secret.dpapi'
if (Test-Path -LiteralPath $secretFile -PathType Leaf) {
    throw 'Segredo DPAPI ja existe. Revisar o provisionamento antes de prosseguir.'
}
$secure = Read-Host -Prompt "Client Secret Keycloak exclusivo do agente $ClientId (oculto)" -AsSecureString
try {
    $encrypted = ConvertFrom-SecureString -SecureString $secure
    [IO.File]::WriteAllText($secretFile,$encrypted,[Text.Encoding]::ASCII)
} finally {
    $encrypted = $null
    if ($null -ne $secure) { $secure.Dispose() }
}
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$acl = Get-Acl -LiteralPath $secretFile
$acl.SetAccessRuleProtection($true,$false)
foreach ($rule in @($acl.Access)) { [void]$acl.RemoveAccessRuleSpecific($rule) }
foreach ($sidValue in @($identity.User.Value,'S-1-5-18','S-1-5-32-544')) {
    $sid = [Security.Principal.SecurityIdentifier]::new($sidValue)
    $rule = [Security.AccessControl.FileSystemAccessRule]::new($sid,[Security.AccessControl.FileSystemRights]::FullControl,[Security.AccessControl.AccessControlType]::Allow)
    [void]$acl.AddAccessRule($rule)
}
Set-Acl -LiteralPath $secretFile -AclObject $acl

# Comprova somente autenticacao, sem buscar/consumir comando pendente.
$secureCheck = ConvertTo-SecureString -String (Get-Content -LiteralPath $secretFile -Raw).Trim()
$ptr = [IntPtr]::Zero
try {
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureCheck)
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    $token = Invoke-RestMethod -Uri $S2sTokenUrl -Method Post -TimeoutSec 15 -ContentType 'application/x-www-form-urlencoded' -Body @{grant_type='client_credentials';client_id=$ClientId;client_secret=$plain}
    if (-not $token.access_token) { throw 'Autenticacao de agente falhou.' }
} catch {
    Remove-Item -LiteralPath $secretFile -Force -ErrorAction SilentlyContinue
    throw 'Nao foi possivel validar token Keycloak: tarefa nao criada.'
} finally {
    $plain = $null
    if ($ptr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
    if ($null -ne $secureCheck) { $secureCheck.Dispose() }
    $token = $null
}
$exe = Join-Path $PSHOME 'powershell.exe'
$args = '-NoLogo -NoProfile -NonInteractive -File "{0}" -ApiBaseUrl "{1}" -S2sTokenUrl "{2}" -ClientId "{3}" -ServerId "{4}" -SecretFile "{5}" -AllowedServices "{6}"' -f $runner,$ApiBaseUrl,$S2sTokenUrl,$ClientId,$ServerId,$secretFile,($names -join ',')
$action = New-ScheduledTaskAction -Execute $exe -Argument $args -WorkingDirectory $installDir
$triggers = @(New-ScheduledTaskTrigger -AtStartup, New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1))
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$password = Read-Host -Prompt "Senha WINDOWS da conta $($identity.Name), com login em lote" -AsSecureString
$ptr2 = [IntPtr]::Zero
try {
    $ptr2 = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
    $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr2)
    if ([string]::IsNullOrWhiteSpace($plainPassword)) { throw 'Senha Windows vazia.' }
    Register-ScheduledTask -TaskName $taskName -Description 'Agente piloto outbound de controle Windows; SOMENTE servicos previamente autorizados' -Action $action -Trigger $triggers -Settings $settings -User $identity.Name -Password $plainPassword -RunLevel Limited -ErrorAction Stop | Out-Null
} finally {
    $plainPassword = $null
    if ($ptr2 -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr2) }
    if ($null -ne $password) { $password.Dispose() }
}
Write-Output ('INSTALADO: ' + $taskName)
Write-Output 'O agente inicia em aproximadamente um minuto; verifique task state Running e logs agent.csv.'
