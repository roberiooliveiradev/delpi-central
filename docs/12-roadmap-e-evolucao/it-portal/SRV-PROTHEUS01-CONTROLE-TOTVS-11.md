# SRV-PROTHEUS01: expansao controlada do agente Windows para 11 servicos TOTVS

**Situacao:** procedimento proposto; NAO autoriza por si so parar ou reiniciar servicos de producao.
**Host:** srv-protheus01
**Server ID:** 6468703b-0faf-4543-af8d-f93f56bd48d6
**Tarefa existente:** Delpi-PortalTI-WindowsControl-SRV-PROTHEUS01
**Conta DPAPI/SCM:** DELPI\ti_delpi
**Cliente Keycloak:** it-portal-windows-control-srv-protheus01

## Inventario confirmado (2026-11-12)

Os 11 estao Running, StartMode Auto, CanStop=True e sem dependentes Windows ativos na consulta SCM. Dependencias de APLICACAO e impacto em usuarios nao foram validados; nao executar stop/restart ate autorizacao operacional.

- appserver_comp
- appserver_rest
- appserver_rest_meu_coletor
- appserver_restMeuProtheus
- appserver_restMinhaProducao
- appserver_salve01
- appserver_salve02
- appserver_salve03
- appserver_salve04
- appserver_schedule
- appserver_ws

Serviço piloto ja homologado e mantido apenas para teste: DelpiPortalControlTest.

## Barreiras de autorizacao independentes

1. **Windows SCM:** conceder somente a DELPI\ti_delpi, por servico, query/status + Start/Stop (SDDL LCSWRPWP), apos backup individual das ACLs e revisao. Nao trocar StartName (LocalSystem, delpi.local\totvs01 etc) nem alterar executaveis ou service config.
2. **API:** atualizar o UNICO registro desse UUID em IT_PORTAL_WINDOWS_CONTROL_TARGETS, acrescentando os 11 nomes por virgula e mantendo o teste e todos os demais servidores. Preservar bindings S2S, client allowlist e feature global. Nunca duplicar entradas para o mesmo UUID, pois o parser da API sobrescreve a anterior.
3. **Agente:** task instalada usa -AllowedServices na acao agendada. Atualizar com Update-ItPortalWindowsServiceControlAgent.ps1 (novo), que valida identidade, caminhos, nomes, faz backup XML da task e altera SOMENTE seus argumentos. Sem recriar cliente Keycloak ou segredo DPAPI.
4. **Pessoa operadora:** exige permissao it-portal.host-services.control e procedimento aprovado para cada parada/reinicio. Controle tecnico nao substitui janela, avaliacao da integracao, backup e plano de recuperacao.

**O instalador inicial antigo possui limite de cinco servicos.** Nao o utilize para sobrescrever a tarefa existente. O novo atualizador aceita ate 25 nomes explicitamente aprovados. Alteracao do instalador para novas maquinas fica para fluxo separado.

## Preflight sem alteracao (Windows)

No PowerShell elevado, sob a MESMA conta que instalou a tarefa:

~~~powershell
whoami
$names = 'DelpiPortalControlTest,appserver_comp,appserver_rest,appserver_rest_meu_coletor,appserver_restMeuProtheus,appserver_restMinhaProducao,appserver_salve01,appserver_salve02,appserver_salve03,appserver_salve04,appserver_schedule,appserver_ws'
$names.Split(',') | ForEach-Object { Get-CimInstance Win32_Service -Filter "Name='$_'" | Select-Object Name,State,StartMode,StartName }
Get-ScheduledTask -TaskName 'Delpi-PortalTI-WindowsControl-SRV-PROTHEUS01' | Select-Object TaskName,State
~~~

Copiar APENAS Update-ItPortalWindowsServiceControlAgent.ps1 da revisao aprovada para WindowsSetup, sem misturar releases. Validar sintaxe local:

~~~powershell
$path = 'C:\Users\ti_delpi\AppData\Local\Delpi\PortalTI\WindowsSetup\Update-ItPortalWindowsServiceControlAgent.ps1'
$tokens=$null; $errors=$null
[void][System.Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)
if ($errors.Count) { $errors; throw 'Script com erro de sintaxe' }
~~~

Simulacao (SEM -Activate, nao altera tarefa):

~~~powershell
$names = 'DelpiPortalControlTest,appserver_comp,appserver_rest,appserver_rest_meu_coletor,appserver_restMeuProtheus,appserver_restMinhaProducao,appserver_salve01,appserver_salve02,appserver_salve03,appserver_salve04,appserver_schedule,appserver_ws'
& $path -ExpectedHostname 'srv-protheus01' -ServerId ([guid]'6468703b-0faf-4543-af8d-f93f56bd48d6') -ClientId 'it-portal-windows-control-srv-protheus01' -TaskName 'Delpi-PortalTI-WindowsControl-SRV-PROTHEUS01' -ApprovedServiceNames $names
~~~

## Janela aprovada: ordem de implantacao

1. Aprovar por escrito o controle dos 11 servicos e a matriz de impacto/janela; garantir restauracao operacional TOTVS.
2. Exportar ACL SDDL original de cada servico; revisar direitos herdados/explicitamente atribuidos; conceder direitos SCM especificos para DELPI\ti_delpi somente nos 11 servicos, com rollback por nome. Essa mudanca nao modifica o estado do servico, mas e critica e precisa de revisao.
3. Atualizar IT_PORTAL_WINDOWS_CONTROL_TARGETS no infra/.env sem excluir SRV-DB01; manter backup seguro do .env. Validar docker compose config --quiet; deploy SOMENTE it-portal-api; verificar container healthy e par UUID/nome no ambiente.
4. No SRV-PROTHEUS01, rodar o atualizador em modo de simulacao e revisar a lista. Com aprovacao, repetir a mesma chamada com -Activate. O programa suspende temporariamente somente a tarefa de controle, altera -AllowedServices, reinicia a tarefa se antes estava Running. Nao executa start/stop/restart de nenhum servico controlado. Confirmar tarefa Running, log sem poll_error e argumentos corretos.
5. Validar negativos no Portal: usuario sem permissão e servico fora da lista nao podem agir; nao testar parada real dos servicos TOTVS durante expediente.
6. Testes funcionais de botoes Iniciar/Parar/Reiniciar somente no DelpiPortalControlTest. Para TOTVS, qualquer parada/reinicio real requer autorizacao propria e plano de recuperacao. Verificar inventario SCM de 5 minutos e inventario host horario intactos.

## Rollback isolado

- **API:** retirar apenas os 11 nomes de IT_PORTAL_WINDOWS_CONTROL_TARGETS neste UUID, preservando DelpiPortalControlTest e a configuracao do SRV-DB01, e atualizar it-portal-api. Nao alterar flag global.
- **Windows:** usar o backup XML gerado em %LOCALAPPDATA%\Delpi\ItPortal\WindowsControl\task-backups como referencia; o atualizador pode ser rodado com -ApprovedServiceNames 'DelpiPortalControlTest' para restaurar allowlist anterior por procedimento aprovado. Em falha na atualizacao, tenta restaurar a task antiga automaticamente.
- **SCM:** restaurar SDDL individual de cada um dos 11 servicos a partir dos backups criados antes da mudanca; nao alterar permissoes ou estado de outros servicos.
- Nunca remover/recriar DPAPI secret, alterar conta da tarefa, interromper o coletor WindowsServices ou fazer deploy geral.

## Criterios de aceite

- [ ] Aprovacao de janela e matriz de impacto TOTVS
- [ ] SDDL original por servico preservado e restore ensaiado
- [ ] Todos os 11 nomes aparecem no unico target do UUID
- [ ] Agente usa identidade/secret originais, tarefa Running
- [ ] Sem ampliacao do escopo do SRV-DB01 nem de servicos Windows nucleares
- [ ] Controles negativos validados e auditoria ativa
- [ ] Coletas horaria e 5 minutos seguem saudaveis
- [ ] Teste de controle no servico piloto, sem parada de producao nao autorizada
