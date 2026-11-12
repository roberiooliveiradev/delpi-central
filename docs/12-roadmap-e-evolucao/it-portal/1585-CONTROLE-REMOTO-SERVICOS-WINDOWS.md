# Chamado #1585 — Controle remoto de serviços Windows em tempo quase real

## Objetivo e separação de responsabilidades
Ações **Iniciar, Interromper e Reiniciar** para serviços Windows explicitamente
permitidos no Portal de TI, inicialmente no SRV-DB01.

- O inventário SCM existente continua a cada **cinco minutos**, sem alterações
  no coletor ou no agendamento original.
- **Novo agente Windows** executa *polling de saída via HTTPS a cada dois segundos*.
  Não expõe portas inbound, não usa WinRM aberto na rede e não recebe scripts
  arbitrários. A ação começa em poucos segundos em condições normais, mas
  **não há promessa de prazo rígido** (rede, Keycloak e estado do Windows).
- A API recebe solicitação de um usuário humano autenticado com permissão
  **it-portal.host-services.control**, revalidada no Core em cada escrita.
- A fila transacional armazena uma solicitação, um único *claim*, e o resultado
  enviado pelo agente com lease aleatório. Não existe retry de comando: em
  falha de confirmação, a interface mostra estado **não confirmado**.
- O agente usa ServiceController para nomes exatos e verifica o estado real
  antes/depois, sem -Force e sem parar dependências. O PostgreSQL só atualiza
  o estado visível quando o Windows informa sucesso.
- Toda solicitação e conclusão normal registram ator, serviço, operação,
  horário, estado anterior/posterior e resultado no histórico do servidor.

## Segurança: bloqueio padrão (obrigatório)
**Não ativar o controle após o merge automaticamente.**
É necessário habilitar explicitamente *todas* as barreiras:

1. Feature flag BFF `IT_PORTAL_WINDOWS_CONTROL_ENABLED=true` (padrão OFF).
2. Allowlist BFF por servidor: `IT_PORTAL_WINDOWS_CONTROL_TARGETS`.
3. Binding S2S por cliente/agente: `IT_PORTAL_WINDOWS_CONTROL_AGENT_BINDINGS`.
4. Cliente Keycloak exclusivo `it-portal-windows-control-srv-db01`
   com audience `it-portal-api`, scope **it-portal.host-services.control-agent**.
5. Permissão humana `it-portal.host-services.control` vinculada a papéis
   de operadores autorizados, junto com `it-portal.servers.view`.
6. Allowlist local do agente e ACLs Windows de conta de serviço com menor
   privilégio possível. Não executar como SYSTEM/administrador, salvo
   aprovação formal e análise de privilégios.
7. Nome aprovado em ambas as allowlists *exatamente igual*, sem wildcard.
   Favoritos e criticidade **não concedem permissões**.

Exemplo de configuração **didática, não liberar em produção sem revisão**:

```text
IT_PORTAL_WINDOWS_CONTROL_ENABLED=false
IT_PORTAL_WINDOWS_CONTROL_TARGETS=<UUID-DO-SERVIDOR>=SERVICO_TESTE
IT_PORTAL_WINDOWS_CONTROL_AGENT_BINDINGS=it-portal-windows-control-srv-db01=<UUID-DO-SERVIDOR>
```

As variáveis ficam no ambiente **real do container** `it-portal-api`,
via Docker Compose. Não basta exportá-las na sessão do SSH.
A configuração vazia continua com todas as ações bloqueadas. Proibidos
serviços nucleares do Windows mesmo com allowlist. Limite inicial de
20 solicitações por servidor/hora e uma ação ativa por serviço.

## Contratos API
### Humanas
- `POST /servers/{server_id}/host-services/{service_name}/actions`
  com `{"action":"restart","request_id":"<UUID>","confirmed":true}`,
  autorização fresh e resposta HTTP 202 (enfileirada, não executada).
- `GET /servers/{server_id}/host-services/actions/{action_id}`:
  `queued | running | succeeded | failed | timeout`.
- `GET /servers/{server_id}/host-services` inclui `control_allowed`;
  `GET /me/capabilities` inclui `can_control_host_services`.
### Agente S2S exclusivo
- `GET /collector/v1/servers/{server_id}/host-services/control/next?hostname=...`:
  solicita um comando com lease aleatório; exige token de escopo exclusivo,
  client bindado ao host, hostname verificado, allowlist e flag ativa.
- `POST /collector/v1/servers/{server_id}/host-services/control/{id}/result`:
  reporta `lease,status,state_after,error_code`. Só um resultado válido
  pode finalizar uma ação. Não confirma sucesso com estado incorreto.

TTL: solicitação ainda não buscada em 30s passa a `timeout`. Comando
reclamado e sem resposta em 75s passa a `timeout`. Em ambas as situações
**não reexecutar sem verificar o estado diretamente no Windows**.

## Frontend
- Botões somente no **detalhe expandido** de serviço presente e permitido;
  não adiciona colunas nem polui a listagem.
- Botões dependem de estado real coletado, capacidade de parar e modo de
  inicialização. O servidor revalida as mesmas precondições.
- Confirmação explícita antes de todas as ações. Feedback visual durante
  fila, execução e retorno confirmado.
- Falha de rede/timeouts **não são exibidos como sucesso**.
- Ações indisponíveis para perfil somente leitura ou servidores arquivados.
- Layout responsivo, foco visível, tokens do tema do Portal de TI e
  animações reduzidas quando solicitado.

## Implantação por etapas (NÃO automática)
1. CI API, UI, PowerShell parse, Postgres real e arquitetura **verdes**.
2. Merge revisado do PR. Backup da base de plugins e janela aprovada.
3. Deploy somente de `it-portal-api` com migration **V008**
   aplicada pelo runner, com flag ainda **false**.
4. Registrar versão **0.3.2** do manifesto `it-portal.manifest.json` no
   Portal Admin pelo fluxo de **nova versão estrutural** (POST register)
   porque adiciona uma permissão. Não usar PUT cosmético.
5. Atribuir `it-portal.host-services.control` apenas ao perfil restrito.
   Deploy do MFE `it-portal`. Com flag false, nenhum comando é permitido.
6. Criar/autorizar novo cliente Keycloak S2S e escopo no BFF.
   Revisar serviço de teste (não Protheus, Minha Produção ou infraestrutura
   essencial). Validar mudanças com administradores do SRV-DB01.
7. Ativar BFF allowlist **apenas** para serviço de teste. Reiniciar somente
   o container it-portal-api, preservando coletor de cinco minutos.
8. Copiar os scripts revisados do PR para o SRV-DB01:
   `Invoke-ItPortalWindowsServiceControlAgent.ps1` e
   `Install-ItPortalWindowsServiceControlAgent.ps1`.
9. Na conta Windows dedicada (DPAPI vinculado a usuário/host), primeiro
   validar a instalação **sem executar nada**:

```powershell
& '.\Install-ItPortalWindowsServiceControlAgent.ps1' -ApprovedServiceNames 'SERVICO_TESTE'
```

   Depois de aprovar o plano, ativar explicitamente:

```powershell
& '.\Install-ItPortalWindowsServiceControlAgent.ps1' -ApprovedServiceNames 'SERVICO_TESTE' -Activate
```

   O instalador pede Client Secret oculto, verifica token de autenticação,
   cifra DPAPI, restringe ACL, pede senha da conta Windows e instala uma
   **tarefa exclusiva** `Delpi-PortalTI-WindowsControl-SRV-DB01`.
   Os scripts ficam no perfil local, sem depender de G:\ ou sessão aberta.

10. Testar um serviço não crítico e dedicado:
    - iniciar (estado parado); comprovar mudança no SCM e Portal;
    - interromper (estado rodando); comprovar resultado;
    - reiniciar; confirmar sucesso e histórico;
    - testar usuário sem permissão, serviço não permitido, agent offline,
      falha/timeout e solicitação duplicada;
    - confirmar que o inventário de 5 min continua atualizando.
11. **Manter #1585 aberto até homologação local e evidências.**

## Rollback seguro
- Desabilitar imediatamente a flag
  `IT_PORTAL_WINDOWS_CONTROL_ENABLED=false` no container API.
- Suspender **somente** a tarefa de controle remoto no Windows:

```powershell
Disable-ScheduledTask -TaskName 'Delpi-PortalTI-WindowsControl-SRV-DB01'
```

- Preservar tabela de ações para auditoria. Não deletar dados
  diretamente, não desfazer migrations já aplicadas.
- Não interromper a tarefa de coleta
  `Delpi-PortalTI-WindowsServices-SRV-DB01`.

## Riscos e limites reconhecidos
- Controle de serviços é operação privilegiada. A conta deve ter direitos
  específicos de Service Control Manager para os nomes selecionados;
  não modificar permissões ou iniciar ações em produção sem aprovação.
- O agente checa dependências para não desligar processos relacionados.
- Reinício executa Stop seguido de Start. Se Start falhar depois do Stop,
  o serviço pode ficar parado; o agente relata falha sem esconder o risco.
- Quando a rede falha após execução, o estado pode ser `timeout` mesmo
  com efeito aplicado. A ação não é repetida por segurança; validar no host.
- Testes CI verificam contratos, transações e sintaxe, não substituem
  a homologação funcional em um Windows Server real.
