# #1576 P2 — Inventario SCM Windows agendado a cada 5 minutos

## Estado e objetivo
O P1 ja foi integrado, a coleta manual no SRV-DB01 foi validada com
263 servicos em 3 lotes e o frontend recebeu redesign (#1580).
Este P2 entrega os scripts e uma politica de retencao. **O merge nao
instala a tarefa no Windows**: ativacao depende de operacao e aceite local.

- Host autorizado: SRV-DB01 (e6b46ca6-7b02-449b-b42e-6ddc498f9894).
- Agenda: a cada **5 minutos**, 24x7, Windows Task Scheduler.
- Tarefa nova: Delpi-PortalTI-WindowsServices-SRV-DB01.
- Cliente S2S exclusivo: it-portal-windows-services-srv-db01, scope
  it-portal.host-services.ingest, audience it-portal-api.
- Metricas/observacoes E4.S4 continuam na tarefa anterior,
  Delpi-PortalTI-Windows-SRV-DB01, sem alteracoes.
- Apenas leitura local Win32_Service e POST de inventario no BFF.
  **Nao inicia, para ou reinicia nenhum servico Windows.**
- Frequencia de 5 minutos significa amostras periodicas, nao monitoramento
  em tempo real nem alerta automatico.

## Retencao do PostgreSQL
A cada coleta completa, a API elimina em pequenos lotes (ate 200)
os registros de execucao e lotes com created_at anterior a 30 dias.
A limpeza e restrita ao proprio servidor da coleta e preserva:
- a execucao em andamento;
- host_service_current.run_id (FK de coleta atual);
- qualquer host_services.last_run_id referenciado por servico
  presente **ou historico**;
- execucoes de outros servidores;
- todos os registros atuais do inventario e outros dominios.

host_service_batches tem ON DELETE CASCADE; so os lotes de runs
elegiveis sao eliminados. O payload de runs completas ja e descartado
(services=NULL) pelo P1; hashes sao retidos ate a expiracao.
Coletas incompletas abandonadas tambem sao elegiveis apos 30 dias.
A limpeza e incremental, nao e uma limpeza integral em todo request.
**Nao modificar a migration V006 ja aplicada**.

## Preparacao no Linux (somente API)
1. Fazer merge do PR apos CI verde.
2. Executar no srv-api:

    cd /home/operador/projetos/delpi-central
    git status --short
    git pull --ff-only origin main

3. Em janela de manutencao autorizada, validar plano e reconstruir
   apenas a BFF alterada:

    ./infra/scripts/up-prod-sequential.sh --dry-run --build it-portal-api
    ./infra/scripts/up-prod-sequential.sh --build it-portal-api

4. Conferir health com:

    docker inspect --format '{{.State.Health.Status}}' delpi-it-portal-api

   Esperado: healthy. A coleta manual anterior nao precisa ser repetida.
5. Nao alterar infra/.env.local; os bindings e allowlists Keycloak ja
   precisam estar funcionando com o cliente exclusivo.

## Instalacao assistida no Windows (apos deploy da API)
**Nao executar instalador E4.S4 existente**: ele atende outro coletor.
A conta Windows que executa o instalador deve ser a mesma que rodara a
tarefa, preferencialmente conta de servico com privilegios minimos
para ler Win32_Service, senha conhecida, permissao Log on as a batch job
e autorizacao para registrar tarefa agendada. Evitar SYSTEM e admin.

1. Copiar estes **quatro arquivos aprovados da mesma revisao** para
   G:\TI\it-portal do SRV-DB01:
   - Collect-ItPortalWindowsServices.ps1
   - Send-ItPortalWindowsServices.ps1
   - Invoke-ItPortalWindowsScheduledServices.ps1
   - Install-ItPortalWindowsScheduledServices.ps1

2. No Windows PowerShell 5.1, com a identidade escolhida para a tarefa:

    Set-Location 'G:\TI\it-portal'
    whoami
    Test-Path '.\Collect-ItPortalWindowsServices.ps1'
    Test-Path '.\Send-ItPortalWindowsServices.ps1'
    Test-Path '.\Invoke-ItPortalWindowsScheduledServices.ps1'
    Test-Path '.\Install-ItPortalWindowsScheduledServices.ps1'

   Todos os Test-Path devem retornar True. Se arquivos aprovados baixados
   vierem com Zone.Identifier, desbloquear **apenas esses quatro** com
   Unblock-File -LiteralPath CAMINHO, sem flexibilizar policy global.

3. Executar:

    & '.\Install-ItPortalWindowsScheduledServices.ps1'

   O instalador verifica srv-db01, sintaxe dos tres scripts, copia o
   pacote para %LOCALAPPDATA%\Delpi\ItPortal\WindowsServices, pede o
   **Client Secret do novo cliente Keycloak** sem eco, salva DPAPI protegido
   por ACL (usuario, SYSTEM, administradores) e faz um envio real com esse
   arquivo. **Falha no smoke nao cria tarefa**.
   Em caso de SMOKE_DPAPI_OK solicita a **senha da conta Windows**,
   distinta do Client Secret, so para registro no Task Scheduler.
   Nunca enviar senhas, JWT ou segredo via chat ou ticket.

4. Esperado TAREFA_REGISTRADA com intervalo 5min. O nome da tarefa
   e diferente do agendamento antigo, que nao deve ser excluido.
   Caminho local evita dependencia do G: sem sessao iniciada.
   MultipleInstances IgnoreNew, StartWhenAvailable, timeout 4min,
   RunLevel Limited. Primeira recorrencia automatica apos ~1min.

## Homologacao obrigatoria no SRV-DB01
Executar separadamente, apos registro:

    Start-ScheduledTask -TaskName 'Delpi-PortalTI-WindowsServices-SRV-DB01'
    Get-ScheduledTask -TaskName 'Delpi-PortalTI-WindowsServices-SRV-DB01' | Select-Object TaskName,State
    Get-ScheduledTaskInfo -TaskName 'Delpi-PortalTI-WindowsServices-SRV-DB01' | Select-Object LastRunTime,LastTaskResult,NextRunTime
    Import-Csv "$env:LOCALAPPDATA\Delpi\ItPortal\WindowsServices\logs\runs.csv" | Select-Object -Last 5

Apos cada execucao, LastTaskResult=0, log status=ok,
batches=3 (se quantidade similar) e novo run_id.
Conferir Ultima coleta no Portal de TI. Aguardar **pelo menos dois**
ciclos (10min) e depois **encerrar a sessao Windows**. Confirmar novo
LastRunTime e run_id com a conta ainda desconectada, antes de
considerar o agendamento homologado. Nao confundir tarefa criada com
execucao desassistida comprovada.

Diagnostico:
- 401/403: secret, escopo, audiencia ou client permitidos no container.
- 409: hostname / allowlist / binding / lote de ingestao.
- Falha sem log: permissao da conta, logon em lote, acesso a pasta local,
  senha Windows, politica de tarefas.
- Secret DPAPI nao decripta: garantir **mesmo usuario e host**. Reprovisionar
  com o mesmo usuario se senha/conta forem alteradas.
- LastTaskResult diferente de zero: inspecionar logs CSV e
  Microsoft-Windows-TaskScheduler/Operational no Event Viewer.
- G: pode nao existir na sessao desassistida: tarefa usa pasta local.
- Log limitado a 1MiB com um anterior. Nunca habilitar transcript com
  payload, token ou credenciais.
- Em incidente, suspender **somente** esta tarefa:

    Disable-ScheduledTask -TaskName 'Delpi-PortalTI-WindowsServices-SRV-DB01'

  Nao interromper Delpi-PortalTI-Windows-SRV-DB01.

## Gatilhos de aceite do P2
- CI API verde, incluida integracao Postgres da retencao.
- Coleta de smoke via DPAPI e tarefa instalada, com 5 minutos.
- Pelo menos 2 execucoes agendadas com LastTaskResult=0 e timestamps
  crescentes na API, uma delas sem sessao conectada.
- Sem logs de segredo, sem perda de inventario atual e sem alterar E4.S4.

## Proximas fases (fora do P2)
Selecao de 2 a 5 servicos monitorados (favoritos persistentes),
deteccao de coleta atrasada, notificacoes, e depois eventual
gerenciamento remoto com RBAC/auditoria/allowlist por servico.
