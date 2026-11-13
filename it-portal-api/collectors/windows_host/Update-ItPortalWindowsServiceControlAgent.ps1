#requires -Version 5.1
<#
.SYNOPSIS
  Atualiza somente a lista local de servicos do agente de controle Windows existente.
.DESCRIPTION
  Simulacao por padrao. A ativacao faz backup XML da tarefa, interrompe apenas
  a tarefa do agente de controle, altera seus argumentos e a inicia novamente.
  Nao modifica servicos Windows, clientes Keycloak, segredos DPAPI, coletores
  de inventario nem autoriza servicos na API. Requer aprovacao de mudanca.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9-]{0,62}$')][string]$ExpectedHostname,
    [Parameter(Mandatory=$true)][guid]$ServerId,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_.-]{3,100}$')][string]$ClientId,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_.-]{5,120}$')][string]$TaskName,
    [Parameter(Mandatory=$true)][string]$ApprovedServiceNames,
    [switch]$Activate
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$hostname = [Environment]::MachineName.ToLowerInvariant()
if ($hostname -ne $ExpectedHostname.ToLowerInvariant()) {
    throw 'Hostname nao corresponde a configuracao aprovada.'
}
if ($hostname -ne 'srv-db01' -and (
    $ClientId -match 'srv-db01' -or
    $ServerId.ToString() -eq 'e6b46ca6-7b02-449b-b42e-6ddc498f9894' -or
    $TaskName -match 'SRV-DB01'
)) {
    throw 'Proibido reaproveitar identidade do piloto em outro host.'
}
$protected = @('rpcss','dcomlaunch','eventlog','plugplay','schedule',
    'winmgmt','samss','lsass','power','profsvc','bfe','mpssvc',
    'lanmanserver','netlogon','wuauserv','cryptsvc')
$names = @($ApprovedServiceNames.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($names.Count -lt 1 -or $names.Count -gt 25) {
    throw 'Informe de 1 a 25 servicos tecnicos explicitamente aprovados.'
}
$unique = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($name in $names) {
    if ($name -notmatch '^[a-zA-Z0-9_.$-]{1,200}$' -or
        $protected -contains $name.ToLowerInvariant() -or
        -not $unique.Add($name)) {
        throw 'Nome de servico invalido, protegido ou duplicado.'
    }
    $service = @(Get-Service -Name $name -ErrorAction Stop | Where-Object { $_.Name -ieq $name })
    if ($service.Count -ne 1) { throw "Servico exato nao encontrado: $name" }
}

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
if ($task.TaskPath -ne '\' -or @($task.Actions).Count -ne 1) {
    throw 'Tarefa fora da raiz ou possui multiplas acoes; requer revisao manual.'
}
$currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$taskSid = ([Security.Principal.NTAccount]$task.Principal.UserId).Translate([Security.Principal.SecurityIdentifier]).Value
if ($taskSid -ne $currentIdentity.User.Value) {
    throw 'Execute sob a mesma identidade Windows da tarefa (DPAPI).'
}
$originalAction = $task.Actions[0]
$expectedExe = Join-Path $PSHOME 'powershell.exe'
if ([IO.Path]::GetFullPath($originalAction.Execute.Trim('"')) -ine [IO.Path]::GetFullPath($expectedExe)) {
    throw 'Executavel de tarefa inesperado.'
}
$agentHome = Join-Path $env:LOCALAPPDATA 'Delpi\ItPortal\WindowsControl'
$runner = Join-Path $agentHome 'Invoke-ItPortalWindowsServiceControlAgent.ps1'
$secret = Join-Path $agentHome 'client-secret.dpapi'
if (-not (Test-Path -LiteralPath $runner -PathType Leaf) -or
    -not (Test-Path -LiteralPath $secret -PathType Leaf)) {
    throw 'Runner ou segredo existente nao encontrado; nao reinstale automaticamente.'
}
$arguments = [string]$originalAction.Arguments
foreach ($expected in @(
    ('-File "' + $runner + '"'),
    ('-ClientId "' + $ClientId + '"'),
    ('-ServerId "' + $ServerId.ToString() + '"'),
    ('-ExpectedHostname "' + $ExpectedHostname + '"'),
    ('-SecretFile "' + $secret + '"')
)) {
    if ($arguments.IndexOf($expected,[StringComparison]::OrdinalIgnoreCase) -lt 0) {
        throw "Identidade ou caminho da tarefa inesperado: $expected"
    }
}
$pattern = '(?i)(?<!\S)-AllowedServices "([^"]*)"'
$matches = [regex]::Matches($arguments,$pattern)
if ($matches.Count -ne 1) { throw 'Parametro AllowedServices ausente ou ambiguo.' }
$oldNames = $matches[0].Groups[1].Value
$newNames = $names -join ','
Write-Output ('AGENTE: ' + $TaskName)
Write-Output ('ATUAL: ' + $oldNames)
Write-Output ('PROPOSTO: ' + $newNames)
if ($oldNames -eq $newNames) {
    Write-Output 'SEM_ALTERACAO: lista local ja corresponde a proposta.'
    return
}
if (-not $Activate) {
    Write-Output 'PREPARADO: nenhuma alteracao aplicada. Exige revisao de seguranca e -Activate.'
    return
}
$elevated = [Security.Principal.WindowsPrincipal]::new($currentIdentity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $elevated) { throw 'Elevacao administrativa obrigatoria para atualizar a tarefa.' }
$newArguments = $arguments.Substring(0,$matches[0].Index) +
    ('-AllowedServices "' + $newNames + '"') +
    $arguments.Substring($matches[0].Index + $matches[0].Length)
$newAction = New-ScheduledTaskAction -Execute $originalAction.Execute -Argument $newArguments -WorkingDirectory $originalAction.WorkingDirectory
$backupDir = Join-Path $agentHome 'task-backups'
New-Item -Path $backupDir -ItemType Directory -Force | Out-Null
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$backup = Join-Path $backupDir ($TaskName + '.' + $stamp + '.xml')
if (Test-Path -LiteralPath $backup) { throw 'Backup ja existe; operacao cancelada.' }
Export-ScheduledTask -TaskName $TaskName -ErrorAction Stop |
    Set-Content -LiteralPath $backup -Encoding UTF8 -ErrorAction Stop
Write-Output ('BACKUP_TAREFA: ' + $backup)
$wasRunning = ($task.State -eq 'Running')
$identityName = $currentIdentity.Name
$securePassword = Read-Host -Prompt "Senha WINDOWS da conta $identityName (oculta)" -AsSecureString
$passwordBstr = [IntPtr]::Zero
try {
    $passwordBstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
    $taskPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordBstr)
    if ([string]::IsNullOrWhiteSpace($taskPassword)) { throw 'Senha vazia; tarefa preservada.' }
    try {
        # A tarefa usa logon por senha. Validar credenciais antes de parar o agente.
        Set-ScheduledTask -TaskName $TaskName -Action $newAction -User $identityName -Password $taskPassword -ErrorAction Stop | Out-Null
        if ((Get-ScheduledTask -TaskName $TaskName).Actions[0].Arguments -ne $newArguments) {
            throw 'Argumentos nao foram persistidos.'
        }
        if ($wasRunning) {
            if ((Get-ScheduledTask -TaskName $TaskName).State -eq 'Running') {
                Stop-ScheduledTask -TaskName $TaskName -ErrorAction Stop
            }
            for ($attempt=0; $attempt -lt 15; $attempt++) {
                if ((Get-ScheduledTask -TaskName $TaskName).State -ne 'Running') { break }
                Start-Sleep -Seconds 1
            }
            if ((Get-ScheduledTask -TaskName $TaskName).State -eq 'Running') {
                throw 'Agente nao encerrou apos Stop-ScheduledTask.'
            }
            Start-ScheduledTask -TaskName $TaskName -ErrorAction Stop
        }
        Write-Output 'ATUALIZADO: agente reconfigurado sem operar servicos Windows.'
        Write-Output ('EXECUCAO_ATUAL: ' + (Get-ScheduledTask -TaskName $TaskName).State)
    } catch {
        $failure = $_
        Write-Warning 'Atualizacao falhou; verificando necessidade de restauracao.'
        try {
            $currentTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
            $currentArgs = [string]$currentTask.Actions[0].Arguments
            if ($currentArgs -ne $arguments) {
                if ($currentArgs -ne $newArguments) { throw 'Argumentos inesperados: revisar tarefa manualmente.' }
                if ($currentTask.State -eq 'Running') { Stop-ScheduledTask -TaskName $TaskName -ErrorAction Stop }
                Set-ScheduledTask -TaskName $TaskName -Action $originalAction -User $identityName -Password $taskPassword -ErrorAction Stop | Out-Null
                if ((Get-ScheduledTask -TaskName $TaskName).Actions[0].Arguments -ne $arguments) {
                    throw 'Rollback nao confirmado.'
                }
                Write-Warning 'Configuracao anterior restaurada.'
            } else {
                Write-Warning 'Configuracao original nao foi alterada.'
            }
            if ($wasRunning -and (Get-ScheduledTask -TaskName $TaskName).State -ne 'Running') {
                Start-ScheduledTask -TaskName $TaskName -ErrorAction Stop
            }
            Write-Warning ('ESTADO_TAREFA: ' + (Get-ScheduledTask -TaskName $TaskName).State)
        } catch {
            Write-Warning ('ROLLBACK_MANUAL_NECESSARIO: ' + $backup)
        }
        throw $failure
    } finally {
        $taskPassword = $null
    }
} finally {
    if ($passwordBstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordBstr)
    }
    if ($null -ne $securePassword) { $securePassword.Dispose() }
}
