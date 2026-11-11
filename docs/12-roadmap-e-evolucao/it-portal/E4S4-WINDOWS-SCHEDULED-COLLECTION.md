# E4.S4 - Coleta Windows agendada (SRV-DB01)

## Objetivo e estado

Automatizar o envio de snapshots tecnicos do SRV-DB01 ao Portal de TI usando
Windows Task Scheduler, sem segredo em texto puro. **O codigo precisa de
homologacao no proprio Windows Server 2019 antes de considerar concluido.**
Nao configura alertas, monitoramento em tempo real, alteracoes no SQL Server,
firewall, reboot, WinRM nem alteracoes em backups.

Piloto E4.S3 ja validado: inventario manual na interface do Portal em
11/11/2026, `source=windows_host_collector`, `status=complete`.

## Modelo de seguranca

- Cliente Keycloak exclusivo: `it-portal-windows-srv-db01`, audience
  `it-portal-api`, escopo `it-portal.observations.ingest`.
- A conta Windows que **instala** deve ser exatamente a mesma que **executa**
  a tarefa. Segredo serializado via `ConvertFrom-SecureString` (DPAPI do Windows,
  escopo da conta/host), protegido por ACL; nunca salvar em .env, linha de
  comando, Git, historico PowerShell ou arquivos de log.
- Tarefa configurada para executar sem sessao interativa, com senha da conta
  passada somente ao registro do Windows Task Scheduler, nunca escrita em
  scripts, command line ou arquivos. Preferir conta de servico dedicada
  nao administrativa, com acesso read-only a WMI/servicos e permissao de logon
  como tarefa em lote. No piloto, a conta de teste deve ter senha conhecida e
  privilegios minimos suficientes.
- Os scripts sao copiados de `G:\TI\it-portal` para
  `%LOCALAPPDATA%\Delpi\ItPortal`; tarefas agendadas nao dependem de
  mapeamentos de unidades. Todos os arquivos sensiveis permanecem no perfil
  local da conta.
- Nunca usar `SYSTEM`, `ExecutionPolicy Bypass`, parametros `-Key` com
  chave AES no repositorio, nem credenciais Linux reaproveitadas.
- DPAPI por usuario pode deixar de funcionar apos troca/reset de senha ou
  mudanca de conta: reconfigurar com a mesma conta da tarefa.

## Instalar apos merge e revisao

1. Atualizar o codigo aprovado (`git pull` no host Git do projeto).
2. Colocar **4 arquivos** juntos em `G:\TI\it-portal`:
   - `Collect-ItPortalWindowsInventory.ps1` (coletor existente).
   - `Send-ItPortalWindowsObservation.ps1` (versao E4.S4, com DPAPI).
   - `Invoke-ItPortalWindowsScheduledObservation.ps1`.
   - `Install-ItPortalWindowsScheduledCollection.ps1`.
3. Conferir origem e integridade. Se houver Zone.Identifier apos download,
   aplicar `Unblock-File` **somente aos arquivos aprovados/revisados**,
   mantendo a politica `RemoteSigned`.
4. Executar interativamente no SRV-DB01 com a conta que sera usada na tarefa:

   ```powershell
   & 'G:\TI\it-portal\Install-ItPortalWindowsScheduledCollection.ps1'
   ```

5. O instalador valida hostname `srv-db01` e sintaxe dos 3 scripts, copia
   para pasta local, pede o Client Secret Keycloak de forma protegida,
   criptografa com DPAPI, restringe ACL do segredo e faz um **smoke real**
   usando `-ClientSecretDpapiPath`. **Se o smoke falhar, nao registra a tarefa.**
6. Ao confirmar `SMOKE_DPAPI_OK`, o instalador solicita a senha da **conta
   Windows atual** para registro no Agendador. Nao usar senha do Keycloak
   nessa segunda pergunta.
7. Tarefa: `Delpi-PortalTI-Windows-SRV-DB01`, execucao a cada **60 minutos**,
   primeira execucao automatica em 5 minutos, repeticao ate 10 anos,
   `StartWhenAvailable`, `MultipleInstances IgnoreNew`, limite de 5
   minutos e `RunLevel Limited`.

## Aceite obrigatorio no servidor (sem colar credenciais)

Apos `TAREFA_REGISTRADA`, executar:

```powershell
Start-ScheduledTask -TaskName 'Delpi-PortalTI-Windows-SRV-DB01'
Get-ScheduledTask -TaskName 'Delpi-PortalTI-Windows-SRV-DB01' |
  Select-Object TaskName, State
Get-ScheduledTaskInfo -TaskName 'Delpi-PortalTI-Windows-SRV-DB01' |
  Select-Object LastRunTime, LastTaskResult, NextRunTime
Import-Csv "$env:LOCALAPPDATA\Delpi\ItPortal\logs\runs.csv" |
  Select-Object -Last 5
```

Esperado apos concluir a execucao: `LastTaskResult = 0`, linha
`status=ok` no CSV, observacao atualizada na pagina do servidor do Portal.
Fechar a sessao de usuario e deixar passar um ciclo horario para validar
**execucao sem logon**, `LastRunTime` avancado, resultado 0 e nova observacao
com `run_id` diferente.

A tela deve manter `source=windows_host_collector`, status `complete` (ou
`partial` quando um subsistema estiver indisponivel) e nova hora de coleta.
Sem a execucao desassistida validada, o E4.S4 nao esta homologado.

## Diagnostico

- `LastTaskResult` diferente de 0: verificar
  `%LOCALAPPDATA%\Delpi\ItPortal\logs\runs.csv` no perfil da mesma conta,
  Event Viewer -> Microsoft-Windows-TaskScheduler/Operational e
  `Get-ScheduledTaskInfo`.
- `http_status` 401/403: validar Client Secret/expiracao, scope e audience.
  Nunca copiar JWT ou segredo em chamados.
- `http_status` 409: allowlist, bindings e/ou hostname do Portal.
- `http_status` 500: logs da API, constraint, migrations ou PostgreSQL.
- Sem logs: validar conta de execucao, direito `Log on as a batch job`,
  senha da conta agendada, perfis locais e permissoes da pasta.
- DPAPI invalida: o instalador protege com a conta Windows que o executa.
  Outra conta nao consegue descriptografar; ajustar identidade e recriar
  o segredo de modo controlado.
- Os logs possuem apenas data, status, estado da coleta, run_id, HTTP status e
  classe da excecao. Arquivos rotacionados a 1 MiB para limitar retencao.
  Nao habilitar transcript completo nem gravar o JSON tecnico.
- Se precisar suspender, sem deletar arquivos ou credenciais:
  `Disable-ScheduledTask -TaskName 'Delpi-PortalTI-Windows-SRV-DB01'`.

## Acompanhamento separado

- Volume I: proximo de 97% de ocupacao: investigar em chamado proprio.
- Divergencia apenas descritiva de sistema operacional, nao bloqueante.
- Rotacionar o segredo Linux previamente exposto, sem interromper indevidamente
  o coletor Linux.
- Warning de collation version do banco `plugins_hub`: plano separado.
- Este agendamento cria **snapshots horarios**, nao alertas automaticos nem
  monitoramento em tempo real; nao confundir esses recursos.
