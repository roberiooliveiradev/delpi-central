# Portal de TI — Runbook de implantação de novos Windows Servers

**Versão:** 1.0 | **Base operacional:** 12/11/2026 | **Piloto homologado:** SRV-DB01  
**Escopo:** cadastro de servidor, inventário técnico (60 min), inventário de serviços SCM (5 min) e controle remoto restrito (~2 s).  
**Regra:** este runbook é o procedimento canônico para os próximos hosts. Os documentos anteriores permanecem como histórico técnico: [E4.S4](E4S4-WINDOWS-SCHEDULED-COLLECTION.md), [#1576 P2](P2-1576-WINDOWS-HOST-SERVICES-SCHEDULED-5MIN.md) e [#1585](1585-CONTROLE-REMOTO-SERVICOS-WINDOWS.md).

## 0. Estado real e limites

- **SRV-DB01:** inventário e controle remoto implantados e homologados pelo operador em 12/11/2026, chamado #1585 solucionado. Não repetir o instalador nesse host: tarefas e DPAPI já existem.
- **Outros servidores:** não estão homologados por este documento. Cada um exige cadastro, credenciais próprias, bindings, revisão de permissões, instalação e aceite independentes.
- O pacote foi adaptado para aceitar parâmetros **ExpectedHostname, ServerId, ClientId e TaskName**. **Somente utilizar em novos servidores após revisão, CI verde e merge deste PR**, e com a configuração individual aprovada. Os padrões ainda apontam ao SRV-DB01 para preservar o piloto e o script recusa sua reutilização em hostname diferente.
- O Portal **não descobre/cadastra novos servidores automaticamente**. Primeiro criar ou localizar manualmente o cadastro e obter seu UUID.
- Nunca testar parada/reinício de serviços críticos, Protheus, Minha Produção, APS, banco, domínio, backups ou rede sem projeto, autorização e janela própria. Controle liberado **por serviço**, não por máquina inteira.
- O agente de controle não substitui as duas tarefas de coleta. Não usa WinRM aberto, portas inbound ou PowerShell remoto arbitrário.

## 1. Arquitetura: três capacidades independentes

| Recurso | Objetivo e periodicidade | Cliente Keycloak / scope | Tarefa Windows |
|---|---|---|---|
| Observações E4.S4 | CPU, memória, volumes, rede, SO, uptime e serviços selecionados; **60 min** | it-portal-windows-NOME / it-portal.observations.ingest | Delpi-PortalTI-Windows-NOME |
| Serviços SCM #1576 | Lista completa Win32_Service, estado, inicialização, AcceptStop; **5 min** | it-portal-windows-services-NOME / it-portal.host-services.ingest | Delpi-PortalTI-WindowsServices-NOME |
| Controle #1585 | Fila de Iniciar/Interromper/Reiniciar; polling HTTPS **~2 s** | it-portal-windows-control-NOME / it-portal.host-services.control-agent | Delpi-PortalTI-WindowsControl-NOME |

NOME é o hostname do novo servidor, em **minúsculas no Client ID** e maiúsculas no nome sugerido da tarefa. Os nomes são exemplos de convenção; usar os mesmos IDs em Keycloak, Compose e instaladores. **Três clientes confidenciais e três segredos distintos por host**. Não clonar secrets, client IDs, tarefas ou UUIDs do SRV-DB01.

A permissão do **usuário humano** é diferente: it-portal.access + it-portal.servers.view + it-portal.host-services.control, restrita aos responsáveis autorizados. Atribuição de favorito/criticidade não concede controle.

## 2. Pré-requisitos e inventário de implantação

Antes de alterar sistemas, registrar em chamado/change por servidor:

| Campo | Exigência |
|---|---|
| Hostname exato | Saída de [Environment]::MachineName.ToLowerInvariant(); deve coincidir com o cadastro no Portal |
| UUID do servidor | UUID **do registro no Portal de TI**, não UUID do hardware nem UUID do piloto |
| Unidade, IP, SO, criticidade, responsável | Conferir com o owner do servidor; não inferir identidade apenas pelo IP |
| Conta Windows de tarefas | Usuário dedicado de menor privilégio, com perfil **local**, PowerShell 5.1, leitura de CIM/WMI, senha gerenciada e direito de executar tarefa em lote |
| Rede/certificados | Saída HTTPS válida para https://minhadelpi.com.br e o Keycloak do realm **delpi**; não abrir WinRM ou inbound |
| S2S | Três Client IDs, três secrets exclusivos e os três client scopes com audience it-portal-api |
| Serviços a controlar | Lista de **nomes técnicos** aprovados, inicialmente apenas 1 serviço de teste não crítico; ACL por serviço documentada e com rollback |
| Janela e evidências | Responsável, aprovação da infraestrutura, backup e resultado dos 3 testes |

Na conta Windows destinada a executar as tarefas (sem prompt de administrador, para testar os direitos reais):

~~~powershell
whoami
$hostname = [Environment]::MachineName.ToLowerInvariant()
$hostname
$PSVersionTable.PSVersion
Get-CimInstance Win32_Service | Measure-Object
~~~

O instalador grava o segredo com **DPAPI vinculado ao usuário e host**. Não execute instaladores com uma identidade e programe a tarefa para outra: o agente não conseguirá ler o segredo. Na hipótese de falta de permissão para registrar tarefas (0x80070005), solicitar à infraestrutura delegação estritamente necessária ou registro administrativo da tarefa com **a mesma conta de execução**; não tornar a conta do agente administradora. A instalação do agente no SRV-DB01 exigiu esse cuidado.

## 3. Criar ou conferir o servidor no Portal

1. Em **Portal de TI > Servidores**, pesquise pelo hostname para **não criar duplicidade**.
2. Se inexistente, cadastre o servidor com o hostname correto e os campos corporativos autorizados.
3. Anote o **UUID interno** do registro do Portal. A API vincula payload de observações e serviços a esse UUID e verifica o hostname recebido.
4. Não sobrescrever manualmente dados curados pelo inventário automático. Observações são evidências, não cadastro autônomo.
5. Ainda **não** habilitar controle de serviço neste novo host.

Defina os parâmetros na sessão do PowerShell 5.1 **uma linha por vez** (substituir os valores ilustrativos antes da execução):

~~~powershell
$hostname = [Environment]::MachineName.ToLowerInvariant()
$hostTag = $hostname.ToUpperInvariant()
$serverId = [guid]'COLE-AQUI-UUID-REAL-DO-PORTAL'
$obsClient = 'it-portal-windows-' + $hostname
$scmClient = 'it-portal-windows-services-' + $hostname
$ctlClient = 'it-portal-windows-control-' + $hostname
$obsTask = 'Delpi-PortalTI-Windows-' + $hostTag
$scmTask = 'Delpi-PortalTI-WindowsServices-' + $hostTag
$ctlTask = 'Delpi-PortalTI-WindowsControl-' + $hostTag
~~~

**Atenção:** COLE-AQUI-UUID-REAL-DO-PORTAL é marcador didático, não comando executável até ser substituído. Nunca reaproveitar o identificador e6b46ca6-7b02-449b-b42e-6ddc498f9894, que pertence ao SRV-DB01.

## 4. Keycloak: credenciais separadas por servidor e capacidade

No console administrativo, selecionar **realm delpi** (não master). Para cada um dos três Client IDs deste host:

1. Criar cliente **OpenID Connect** com Client Authentication e Service Accounts habilitados; fluxos de navegador/senha desnecessários desativados.
2. No realm delpi, confirmar ou criar os *client scopes* de ingestão/controle exatos da tabela acima. Em cada scope criar um mapper **Audience** com **Included Custom Audience = it-portal-api**, incluindo no **access token**.
3. Associar **somente o scope necessário** ao respectivo cliente como **Default**; o agente solicita grant_type=client_credentials sem enviar scope explicitamente.
4. Avaliar o token, sem compartilhar JWT ou secret: **iss** termina em /realms/delpi, **azp** identifica o cliente certo, **aud** inclui it-portal-api e **scope** inclui a permissão S2S correta.
5. Guardar cada Client Secret no canal corporativo de segredos, somente para digitação local protegida durante instalação. **Nunca** usar o segredo do realm master, do SRV-DB01 ou de outro consumidor.

Os clientes para observações, serviços SCM e controle **não são substitutos entre si**.

## 5. Linux: adicionar binding sem remover o piloto

No srv-api, inspecionar previamente as linhas existentes em infra/.env e salvar cópia segura do arquivo sob os controles internos. **Não publicar o conteúdo do .env em chat, chamados, commits ou prints**, pois ele contém segredos de outros sistemas.

~~~bash
cd /home/operador/projetos/delpi-central
git status --short
git pull --ff-only origin main
grep -E '^(IT_PORTAL_S2S_ALLOWED_CLIENTS|IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST|IT_PORTAL_WINDOWS_COLLECTOR_BINDINGS|IT_PORTAL_WINDOWS_CONTROL_ENABLED|IT_PORTAL_WINDOWS_CONTROL_TARGETS|IT_PORTAL_WINDOWS_CONTROL_AGENT_BINDINGS)=' infra/.env
~~~

No infra/.env, **preservar todos os clientes e servidores atuais**. Acrescentar:

- **IT_PORTAL_S2S_ALLOWED_CLIENTS:** lista separada por **vírgula**; adicionar os três novos Client IDs sem excluir os existentes.
- **IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST:** lista de UUIDs separada por **vírgula**; acrescentar o novo UUID.
- **IT_PORTAL_WINDOWS_COLLECTOR_BINDINGS:** pares **client_id=uuid** separados por **ponto e vírgula**; criar **dois pares**, para o cliente de observações e o cliente SCM deste host.
- **IT_PORTAL_WINDOWS_CONTROL_AGENT_BINDINGS:** só na fase de controle, par client_id-controle=uuid, separado por ponto e vírgula dos anteriores.
- **IT_PORTAL_WINDOWS_CONTROL_TARGETS:** só na fase de controle, par uuid=SERVICO_TESTE; serviços de um mesmo servidor separados por vírgula, servidores por ponto e vírgula.
- **IT_PORTAL_WINDOWS_CONTROL_ENABLED:** flag **global**. O piloto já a utiliza; não alterná-la indiscriminadamente. Novo host permanece bloqueado sem target e binding mesmo se a flag global for true.

Exemplo **abstrato** mostrando apenas o acréscimo, não substituir as linhas existentes:

~~~dotenv
IT_PORTAL_S2S_ALLOWED_CLIENTS=CLIENTES_EXISTENTES,it-portal-windows-novo,it-portal-windows-services-novo,it-portal-windows-control-novo
IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST=UUIDS_EXISTENTES,UUID_NOVO
IT_PORTAL_WINDOWS_COLLECTOR_BINDINGS=BINDINGS_EXISTENTES;it-portal-windows-novo=UUID_NOVO;it-portal-windows-services-novo=UUID_NOVO
IT_PORTAL_WINDOWS_CONTROL_AGENT_BINDINGS=BINDINGS_CONTROLE_EXISTENTES;it-portal-windows-control-novo=UUID_NOVO
IT_PORTAL_WINDOWS_CONTROL_TARGETS=TARGETS_EXISTENTES;UUID_NOVO=SERVICO_TESTE_APROVADO
~~~

A última dupla de linhas **somente entra depois da autorização** para o serviço piloto do novo host. **UUID_NOVO etc. são placeholders** e não devem ser gravados literalmente.

Verificar a configuração antes de subir, com API do Portal de TI apenas:

~~~bash
./infra/scripts/up-prod-sequential.sh --dry-run it-portal-api
./infra/scripts/up-prod-sequential.sh it-portal-api
docker inspect --format '{{.State.Health.Status}}' delpi-it-portal-api
~~~

Esperado: healthy. Se houve alterações de código e o deploy ainda não ocorreu, usar --build especificamente no it-portal-api. Não fazer deploy geral.

## 6. Pacote e diretórios Windows

Obter **todos os scripts de uma mesma revisão aprovada** do diretório:
[it-portal-api/collectors/windows_host](../../../it-portal-api/collectors/windows_host).

**Observações E4.S4 (4):**
- Collect-ItPortalWindowsInventory.ps1
- Send-ItPortalWindowsObservation.ps1
- Invoke-ItPortalWindowsScheduledObservation.ps1
- Install-ItPortalWindowsScheduledCollection.ps1

**Serviços SCM #1576 (4):**
- Collect-ItPortalWindowsServices.ps1
- Send-ItPortalWindowsServices.ps1
- Invoke-ItPortalWindowsScheduledServices.ps1
- Install-ItPortalWindowsScheduledServices.ps1

**Controle #1585 (2):**
- Invoke-ItPortalWindowsServiceControlAgent.ps1
- Install-ItPortalWindowsServiceControlAgent.ps1

Copiar todos os dez para uma pasta local de preparação revisada (ex.: C:\ProgramData\Delpi\PortalTI\WindowsSetup), acessível à conta da tarefa. Não confiar em letra G: dentro de sessão sem logon. Revisar origem, hash/revisão e assinatura política; caso haja Zone.Identifier, aplicar **Unblock-File somente aos dez arquivos verificados**; nunca desabilitar ExecutionPolicy globalmente.

~~~powershell
Set-Location 'C:\ProgramData\Delpi\PortalTI\WindowsSetup'
Get-ChildItem -Filter '*.ps1' | Select-Object Name
~~~

O instalador copia os runners para %LOCALAPPDATA%\Delpi\ItPortal (observações), %LOCALAPPDATA%\Delpi\ItPortal\WindowsServices (SCM) e %LOCALAPPDATA%\Delpi\ItPortal\WindowsControl (controle). Cada um usa secret DPAPI distinto sob a **mesma conta Windows**.

## 7. Instalar primeiro a coleta técnica horária

Com os parâmetros da seção 3 e o **cliente de observações** criado, executar na conta final:

~~~powershell
& '.\Install-ItPortalWindowsScheduledCollection.ps1' -ExpectedHostname $hostname -ServerId $serverId -ClientId $obsClient -TaskName $obsTask
~~~

O instalador confere identidade/arquivos, solicita Client Secret oculto, grava DPAPI com ACL restrita, envia um **smoke** HTTPS real e só então solicita senha Windows para registrar a tarefa. Esperado: SMOKE_DPAPI_OK e TAREFA_REGISTRADA.

~~~powershell
Start-ScheduledTask -TaskName $obsTask
Get-ScheduledTaskInfo -TaskName $obsTask | Select-Object LastRunTime,LastTaskResult,NextRunTime
Import-Csv "$env:LOCALAPPDATA\Delpi\ItPortal\logs\runs.csv" | Select-Object -Last 5
~~~

Conferir na página do servidor: nova observação, source=windows_host_collector, horário, dados técnicos e status complete/partial conforme disponibilidade. Exigir execução sem sessão de usuário aberta em ciclo posterior. Não interpretar Ready isoladamente como coleta bem-sucedida.

## 8. Instalar o inventário SCM de cinco minutos

Depois que a API tiver o novo collector binding, e com o **cliente SCM** específico:

~~~powershell
& '.\Install-ItPortalWindowsScheduledServices.ps1' -ExpectedHostname $hostname -ServerId $serverId -ClientId $scmClient -TaskName $scmTask
~~~

Esperado: SMOKE_DPAPI_OK e TAREFA_REGISTRADA. A coleta é read-only e NÃO controla serviços.

~~~powershell
Start-ScheduledTask -TaskName $scmTask
Get-ScheduledTaskInfo -TaskName $scmTask | Select-Object LastRunTime,LastTaskResult,NextRunTime
Import-Csv "$env:LOCALAPPDATA\Delpi\ItPortal\WindowsServices\logs\runs.csv" | Select-Object -Last 5
~~~

No Portal: lista completa de serviços, quantidade, estado, modo, presença, favoritos/criticidade e última coleta. Verificar ao menos **dois ciclos** de 5 minutos, sendo um com sessão desconectada. O número de serviços não precisa ser igual aos 263 do SRV-DB01.

## 9. Controle remoto: somente após homologar as duas coletas

1. Selecionar e aprovar um **serviço não crítico de teste** neste host. Registrar nome técnico real, dependências e operação de retorno. Não instalar serviço de teste automaticamente em servidor de produção sem aprovação.
2. Confirmar que a conta de tarefa pode **iniciar, parar e reiniciar somente esse serviço**, usando permissões SCM granulares aprovadas pela infraestrutura. **Não copiar SDDL/SIDs do piloto**, nem alterar a DACL de serviços críticos. Fazer backup da DACL original e prever reversão antes de qualquer ajuste.
3. Confirmar cliente S2S de controle (scope correto no realm delpi), permissão humana it-portal.host-services.control, manifesto do Portal com essa permissão, e introduzir bindings e target específicos no infra/.env **sem remover o piloto**; subir somente it-portal-api.
4. Executar primeiro um **dry-run sem mudanças**:

~~~powershell
& '.\Install-ItPortalWindowsServiceControlAgent.ps1' -ExpectedHostname $hostname -ServerId $serverId -ClientId $ctlClient -TaskName $ctlTask -ApprovedServiceNames 'SERVICO_TESTE_APROVADO'
~~~

Esperado: PREPARADO e nenhuma alteração. Apenas depois de conferir todos os valores, permitir ativação:

~~~powershell
& '.\Install-ItPortalWindowsServiceControlAgent.ps1' -ExpectedHostname $hostname -ServerId $serverId -ClientId $ctlClient -TaskName $ctlTask -ApprovedServiceNames 'SERVICO_TESTE_APROVADO' -Activate
~~~

Secret Keycloak e senha Windows são solicitados **separadamente, ocultos**. A tarefa roda com privilégios limitados e polling de saída HTTPS. Se o registro terminar com **0x80070005**, **não** recriar o Client Secret nem elevar permanentemente o usuário; consultar o Agendador/política e seguir procedimento de registro pela infraestrutura usando a mesma conta e os mesmos argumentos, preservando DPAPI.

~~~powershell
Get-ScheduledTask -TaskName $ctlTask | Select-Object TaskName,State
Get-ScheduledTask -TaskName $ctlTask | Select-Object -ExpandProperty Principal
Get-ScheduledTaskInfo -TaskName $ctlTask | Select-Object LastRunTime,LastTaskResult
~~~

Se Ready, iniciar; se Running, não duplicar:

~~~powershell
Start-ScheduledTask -TaskName $ctlTask
Import-Csv "$env:LOCALAPPDATA\Delpi\ItPortal\WindowsControl\logs\agent.csv" | Select-Object -Last 10
~~~

O agente carrega explicitamente **System.ServiceProcess**; esta correção é necessária em sessões sem profile (PR #172). Ao confirmar sucesso, o agente reporta state_after **e can_stop**, atualizados atomicamente na API para habilitar Interromper/Reiniciar sem aguardar próxima coleta SCM (PR #173).

### Homologação funcional e segurança

No Portal, em **Servidores > [host] > Serviços Windows > detalhes do serviço de teste**:
1. Serviço parado: **Iniciar** → confirmado pelo Windows → Running; conferir no Get-Service e no histórico.
2. Serviço rodando e parável: **Interromper** → Stopped; conferir imediatamente.
3. **Iniciar** novamente, depois **Reiniciar** → Running; confirmar histórico, estados e botões.
4. Usuário sem permissão: controle não visível/403. Serviço fora da allowlist: não pode ser acionado. Hostname e Client ID de outro host: acesso negado.
5. Simular indisponibilidade somente de modo controlado, verificar timeout sem sucesso falso e **sem repetição automática**.
6. Confirmar coletas E4.S4 (horária) e SCM (5 min) ainda funcionando. Guardar prints dos estados, horários, task status e auditoria **sem credenciais**.

Não concluir onboarding sem passar os gates. **Feature global ativa não significa autorização de um serviço não listado.**

## 10. Diagnóstico e rollback sem interromper outros servidores

| Sintoma | Investigar |
|---|---|
| 401/403 na ingestão | Realm delpi, credencial individual, scope Default, audience it-portal-api, IT_PORTAL_S2S_ALLOWED_CLIENTS e permissão humana quando aplicável |
| 409 | UUID, hostname cadastrado, binding client→servidor, allowlist, serviço ou precondição |
| Ready ou 0x800710E0 no Scheduler | Instância já em execução/IgnoreNew; validar estado real e logs, não presumir falha |
| 0x80070005 ao registrar | Direitos de registrar tarefa e logon em lote; registro por infraestrutura sem mudar DPAPI de identidade |
| Poll_error no agente | Token, endpoint, feature flag, allowlists/binding, conectividade; resultado action=succeeded prova comunicação funcional |
| execution_failed / TypeNotFound | Verificar agente atualizado com Add-Type -AssemblyName System.ServiceProcess |
| Estado Running mas Stop/Restart desabilitados | Verificar can_stop real e atualização da API/agent (PR #173); recarregar e checar coleta |
| LastTaskResult diferente de 0 | Ler CSV apropriado, Task Scheduler/Operational, conta, path local e secret DPAPI |

**Rollback do controle de somente um host**: remova o par **do novo host** de IT_PORTAL_WINDOWS_CONTROL_TARGETS e de IT_PORTAL_WINDOWS_CONTROL_AGENT_BINDINGS, preservando SRV-DB01; aplicar a configuração em it-portal-api. No novo Windows, suspender **somente**:

~~~powershell
Disable-ScheduledTask -TaskName $ctlTask
~~~

Se também precisar suspender coleta **somente deste novo host**:

~~~powershell
Disable-ScheduledTask -TaskName $scmTask
Disable-ScheduledTask -TaskName $obsTask
~~~

Não desligar globalmente IT_PORTAL_WINDOWS_CONTROL_ENABLED para desfazer apenas um novo host: isso interromperia o piloto e demais hosts. Não alterar tabelas diretamente nem apagar trilha de auditoria. Para restaurar, revisar risco/segredo e usar Enable-ScheduledTask apenas após resolução. Rotacionar Client Secret com procedimento por identidade Windows e janela; o DPAPI não é copiável entre contas/hosts.

## 11. Checklist de aceite por servidor

- [ ] Cadastro de servidor único; hostname e UUID conferidos com o próprio Windows
- [ ] Responsável, criticidade, aprovação, conta e HTTPS documentados
- [ ] Três clientes Keycloak individuais com Default scopes, audience e autorização no BFF
- [ ] Variáveis no infra/.env estendidas **sem excluir** bindings/targets existentes
- [ ] Coleta horária: smoke, execução agendada e execução sem sessão confirmados
- [ ] Serviços SCM: smoke, dois ciclos, execução desconectada e lista completa confirmados
- [ ] Serviço de teste não crítico aprovado; conta com direitos SCM específicos e backup de ACL
- [ ] Controle: dry-run, instalação e tarefa Running com conta Limited
- [ ] Start, Stop, Restart, estado/can_stop e auditoria confirmados no Windows + Portal
- [ ] RBAC negativo, serviço não autorizado, host não autorizado, timeout e logs validados
- [ ] Evidências anexadas ao chamado; responsável registra aprovação de expansão

**Referências de implantação:** [E4.S3](E4S3-WINDOWS-OBSERVATIONS.md) · [E4.S4](E4S4-WINDOWS-SCHEDULED-COLLECTION.md) · [#1576 P2](P2-1576-WINDOWS-HOST-SERVICES-SCHEDULED-5MIN.md) · [#1585](1585-CONTROLE-REMOTO-SERVICOS-WINDOWS.md).  
**Alteração de segurança por novo servidor é sempre específica.** Este documento não autoriza automaticamente novos serviços ou hosts em produção.
