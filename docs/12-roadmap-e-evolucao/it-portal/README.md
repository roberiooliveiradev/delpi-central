# Portal de TI — ledger de etapas

Estado de entrega e aceite do Portal de TI (`plugins/it-portal` + `it-portal-api`).
Arquitetura, contrato e permissões vigentes: `it-portal-api/README.md` e
`plugins/it-portal/README.md`. Histórico de implementação fica no Git.

## Etapas

| Etapa | Escopo | Commit | Estado | Aceite |
|---|---|---|---|---|
| E1 — `IT-PORTAL-MVP-E1` | Servidores, anotações, planos de ação, visão geral | `5df2177c` | COMPLETE | aceito pelo PO |
| Gate 0 recovery | Recuperação do baseline em produção | `85626954` | COMPLETE_WITH_RESIDUAL | `REVIEW_DECISION: ACCEPT_WITH_RESIDUAL` |
| E2A — `IT-PORTAL-INVENTORY-E2A` | Serviços/aplicações, instâncias de banco, hospedagem serviço→servidor, consumo serviço→banco | `a656d209` | COMPLETE_WITH_RESIDUAL | `REVIEW_DECISION: ACCEPT_WITH_RESIDUAL` — homologado em produção pelo PO com os sete critérios funcionais confirmados |
| R-SEC-01 | Residual RBAC das escritas (ver abaixo) | `d39f6012` | implementado antes da E2B | pendente de revisão |
| E2B — `IT-PORTAL-INVENTORY-E2B` | Redes, integrações e relacionamentos entre recursos (ver abaixo) | ver Git | implementado | pendente de revisão |
| E3A — mapa visual | Visualização interativa de dependências entre ativos | — | PLANNED — projeto futuro, adiado pelo PO | Não iniciar na prioridade atual |
| E3B — análise de impacto | Simulação de indisponibilidade e dependências afetadas | — | PLANNED — projeto futuro, adiado pelo PO | Não iniciar na prioridade atual |
| E4 — coleta automática de inventário | Descoberta e atualização periódica de servidores Windows/Linux, redes e infraestrutura Sophos, com proveniência e reconciliação | — | PLANNED — prioridade atual para discovery/arquitetura | Decisão do PO em 10/11/2026; implementação ainda não iniciada |

O executor não se auto-aceita: o estado de aceite é registrado somente após
`REVIEW_DECISION` do Product Owner.

## R-SEC-01 — residual RBAC das escritas

Evidência (código, antes da correção):

- `shared/delpi_auth/middleware/fastapi_auth.py` resolve permissões do Core
  `/me` com cache de 60 s e fallback stale de até 15 min quando o Core falha;
  todas as escritas do `it-portal-api` usavam esse principal, então uma
  permissão revogada ainda podia gravar dentro dessa janela.
- As escritas de servidor exigiam apenas `it-portal.servers.manage`, enquanto
  `/me/capabilities` só concede `can_manage_servers` com
  `it-portal.servers.view`: o backend permitia mais que a capability declarada.

Correção (owner-local, `it-portal-api/.../interface/http/authz.py`):

- `authorize_write` = `authorize` + `load_user_rbac(force_refresh=True)` (sem
  cache, sem stale, fail-closed → 503); o principal fresh é o autor auditado;
- escritas de servidor exigem `servers.view` + `servers.manage`;
- leituras permanecem no caminho com cache (sem mudança de latência).

Testes: `it-portal-api/tests/test_http_write_authz.py` (revogação após cache
bloqueia todas as escritas; Core indisponível no lookup fresh → 503 sem
gravar; leituras não fazem lookup fresh; manage sem view → 403).

Fora do escopo: o bypass `is_superadmin` de `delpi_auth.authz_core` é
comportamento canônico da plataforma e não é alterado pelo Portal de TI.

## E2B — decisões de modelagem

- **Redes** (`networks`, migration `V003`): CIDR validado no backend e no banco
  (`::cidr`), gateway dentro do CIDR, VLAN 1–4094. O escopo
  `container_runtime` é a confirmação explícita exigida para redes do Docker;
  elas nunca são tratadas como corporativas. CIDR único por unidade apenas
  entre redes corporativas ativas. Sem varredura.
- **Conectividade** servidor↔rede (`server_network_links`): IP opcional, dentro
  do CIDR, sem endereço de rede/broadcast; alterar o CIDR é recusado se deixar
  IPs vinculados fora.
- **Integrações** (`integrations`): origem e destino são um serviço cadastrado
  ou um sistema externo nomeado, com pelo menos uma ponta interna e sem
  autointegração; protocolo e direção em catálogo; texto passa pelo guard de
  segredos. Consumo de banco continua em `database_consumers`.
- **Dependência operacional** serviço→serviço (`service_dependencies`): somente
  registrada explicitamente, sem autorrelação nem duplicata.
- Hospedagem, conectividade, consumo e dependência são tipos distintos; a
  página do servidor deriva as integrações das hospedagens. Mapa e análise de
  impacto ficam para a E3.
- Correção incidental da E2A: o histórico do MFE lia `changes.database`, mas a
  API grava o snapshot do vínculo serviço–banco como `database_instance`.

## Inventário GLPI / Zabbix (E2A e E2B)

| Capacidade | GLPI no repositório | Zabbix | Decisão |
|---|---|---|---|
| Servidores, serviços, instâncias de banco (E2A) | não consumidos | sem referência | Portal de TI é owner do cadastro |
| Redes lógicas (CIDR/VLAN/gateway) | não consumidas (`IPNetwork`/`Network` sem uso) | sem referência | Portal de TI é owner do cadastro |
| Equipamento de rede físico | `NetworkEquipment` apenas para vincular chamados no `helpdesk-api` | sem referência | não duplicado; fora do escopo da E2B |
| Integrações e relacionamentos | não consumidos | sem referência | Portal de TI é owner do cadastro |

Uso real do GLPI: somente `helpdesk-api` (chamados e vínculo de ativos ao
chamado, `helpdesk_app/infrastructure/glpi/mapping.py`). Nenhuma integração
automática GLPI/Zabbix é feita pelo Portal de TI.

## Repriorização de roadmap pelo PO — 10/11/2026

**Decisão:** postergar E3A e E3B para projetos futuros. Priorizar E4, inventário automatizado, antes de construir mapa gráfico e motor de impacto. Essa mudança **não equivale a aceite adicional da E2B** nem autoriza execução de código, integração ativa ou alteração de infraestrutura.

**Fonte inventariada — Matriz (PROVEN pela captura de tela fornecida pelo PO em 10/11/2026):**
- Firewall principal: **Sophos XGS 116**, firmware **SFOS 21.5.0 GA, Build 171**. O modelo/firmware da filial **não foi confirmado** e deve ser inventariado separadamente. Não registrar número de série da imagem no roadmap.
- **TARGET de integração:** estudar API **XML** do SFOS 21.5 (operações exclusivamente de consulta; acesso desabilitado por padrão, liberar apenas IP do coletor, conta própria com perfil restrito somente leitura quando comprovado) e **SNMPv3** para métricas de saúde; não assumir disponibilidade da API REST lançada nas versões mais novas.
- **TO_INVENTORY:** versão/habilitação efetiva de API e SNMP, MIBs, endpoints/entidades consultáveis, IP e zona do coletor, permissões administrativas, campos de redes/interfaces/VLAN/rotas e cobertura real; configuração em ambiente controlado sem varredura irrestrita.
- **STOP:** qualquer necessidade de alterar regras/políticas de firewall, usar credencial administrativa ampla ou coletar segredos exige revisão de segurança e autorização específica. Não inferir ativos Windows/Linux a partir de objetos de rede do Sophos.
- Fontes técnicas oficiais: https://docs.sophos.com/nsg/sophos-firewall/21.5/Help/en-us/webhelp/onlinehelp/AdministratorHelp/BackupAndFirmware/API/APIConfiguration/index.html e https://docs.sophos.com/nsg/sophos-Firewall/21.5/help/en-us/webhelp/onlinehelp/AdministratorHelp/Administration/SNMP/index.html .

**Direção operacional do PO — coleta interna independente (10/11/2026):**
- A TI interna da DELPI, sob responsabilidade do PO, deve operar e governar o inventário automático e suas credenciais. O GLPI operado pela empresa terceirizada **não é dependência nem condição de execução** e não deve ser consultado como pré-requisito para iniciar.
- O GLPI da própria DELPI pode ser inventariado e reutilizado **apenas se houver ganho demonstrado e acesso autorizado**, sem criar autoridade paralela; inventariar ferramentas/agentes já presentes nos hosts antes de instalar novos.
- **Primeiro piloto: servidor Linux `srv-api`**, já cadastrado no Portal de TI. Iniciar por diagnóstico local e comandos read-only executados pelo responsável interno, sem modificar daemon, pacotes, permissões, SSH, firewall, Docker ou configuração produtiva.
- Levantar SO/kernel, hardware, memória, disco, interfaces, serviços/systemd, containers Docker, agentes existentes e mecanismos seguros de identificação. Evidência obtida manualmente em terminal serve de baseline, **não prova integração automática**.
- Só após inventário e revisão de segurança escolher o adaptador: coletor local mínimo, agente já instalado, SSH com chave/conta restrita ou API existente. Planejar Windows depois; Sophos Matriz SFOS 21.5 depois. Não iniciar captura remota ativa sem contrato, credenciais e allowlist aprovados.
- Coletar observações com `source`, `observed_at`, identidade estável e conciliação idempotente contra cadastros preexistentes. Dados curados manualmente não são sobrescritos; divergências viram candidatos para revisão. A Etapa 3A/3B permanece adiada.

**E4 / piloto srv-api — evidência de diagnóstico local (10/11/2026, PROVEN na saída fornecida pelo PO):**
- Host Linux com Zabbix Agent 2 **7.0.23**, serviço `zabbix-agent2` ativo e habilitado. Hostname e memória disponível retornaram valores no teste `-t`; `system.cpu.num` retornou `ZBX_NODATA` (**INCONCLUSIVE**, não caracteriza falha do serviço sem verificação adicional).
- Zabbix `Server`, `ServerActive` e `Hostname` configurados (destinos não expostos; **owner do servidor Zabbix e acesso à API ainda TO_INVENTORY**). Não concluir que a DELPI já controla a fonte de monitoramento.
- Docker em operação com **114 containers** observados no instante da coleta. A lista de redes revelou `inventario-ti_default`: indício de projeto de inventário pré-existente, mas **TO_INVENTORY** quanto a containers, finalidade, manutenção e reuso. Não criar outro coletor até inspecionar essa capacidade.
- Os testes foram apenas leituras locais; **não existe comprovação de coleta automatizada integrada ao Portal de TI**. Recomendação: verificar containers e labels Compose da rede `inventario-ti_default` e a capacidade Zabbix antes de escolher implementação, sem adicionar acesso/credenciais nem modificar serviços.
- **Risco operacional observado:** swap totalmente utilizada e disco principal próximo de 83% na amostra anterior; exigir orçamento de recursos, volume, agendamento controlado e fail-safe no piloto.

**E4 / inspeção `inventario-ti_default` (10/11/2026, PROVEN na saída do PO):**
- Rede Docker `inventario-ti_default` identificada como projeto Compose `inventario-ti` com **dois containers somente**: `inventario-ti-glpi-1` (imagem `glpi/glpi:latest`, running) e `inventario-ti-db-1` (imagem `mysql:9.6`, healthy). Portanto, trata-se de **GLPI e banco**, e não de um coletor de infraestrutura já confirmado. Nenhum agente GLPI Linux foi demonstrado nesse levantamento.
- O projeto pode ser o GLPI interno da DELPI, conforme o contexto do PO, mas exigem confirmação sua identidade/instância, versão, inventário nativo habilitado, ativos/agents existentes e acesso de API com least privilege. O `latest` da imagem **não comprova versão GLPI instalada**.
- O `srv-api` tem 16 CPUs lógicas via `nproc`, Zabbix Agent 2 v7.0.23 operante; a chave local `system.cpu.num` permaneceu inconclusiva. Não transformar essa exceção em bloqueio para inventário.
- **Gate seguinte somente leitura:** inspeção no GLPI interno pela UI (versão, Administração > Inventário, Ativos > Computadores e agentes/últimas coletas), sem instalar agente, executar varredura ou editar configuração. Depois decidir `EXISTING_EQUIVALENT`/`REUSE_DECISION` para a coleta do Linux e a integração autorizada GLPI → Portal de TI.
- Modelo proposto (TARGET, ainda não decidido): GLPI interno como possível fonte de **observações** de hardware/software via agente; Portal de TI preserva cadastro e relações curadas, reconciliando por identidade estável, com trilha de proveniência e aprovação de divergências. Não presumir vínculo direto ao MySQL do GLPI.

**Decisão de escopo superveniente do PO — somente servidores (10/11/2026):**
- **Prioridade E4:** mapear e automatizar somente servidores Linux e Windows da DELPI, começando pelo `srv-api` (Linux) já cadastrado no Portal de TI. Cadastro e gerenciamento dos servidores devem continuar no domínio do `it-portal-api` e MFE `it-portal`.
- **FORA DO ESCOPO AGORA:** computadores, notebooks, estações de trabalho e migração do inventário de computadores já cadastrado manualmente no GLPI da DELPI. Não criar telas, agentes ou migrations para endpoints de usuário nesta fase.
- **Evidência declarada pelo PO:** os servidores ainda **não foram mapeados no GLPI interno**; portanto **não exigir consulta ao GLPI ou instalação de GLPI Agent** para iniciar a coleta de servidores. A verificação de UI do GLPI citada no diagnóstico anterior fica **cancelada como próximo gate**. A presença dos containers `inventario-ti-glpi-1`/`inventario-ti-db-1` não demonstra coleta de servidores.
- **Reuse gate restrito:** aproveitar dados locais e capacidades autorizadas do Linux, Zabbix Agent 2 (se tecnicamente viável sem depender do monitoramento de terceiros), Docker e ferramentas Windows já existentes. Escolher adaptador somente após avaliar permissões, limites, owners, consumo de recursos, contratos e segurança. Proibir criação duplicada de servidor e sobrescrita silenciosa de campos manuais.
- **Entrega alvo:** coleta periódica somente leitura com origem/horário/estado, reconciliação idempotente com servidor existente, revisão de divergências e visibilidade no Portal de TI; iniciar em modo observação/dry-run antes de qualquer escrita no inventário. Sem acesso remoto privilegiado, varredura indiscriminada ou novas dependências de terceirizados.
- A E3A/E3B permanece futura, e a integração Sophos segue posterior ao primeiro piloto de servidores. O inventário existente de computadores no GLPI não será alterado por este projeto.

**Objetivo da E4 (PLANNED):** minimizar o cadastro manual de servidores Windows/Linux e da infraestrutura de rede Sophos, sem criar uma segunda autoridade sobre ativos existentes, nem sobrescrever dados operacionais curados por pessoas.

**Gate inicial (TO_INVENTORY), antes de aprovar contratos/implementação:**

- Reancorar em GitHub HEAD, regras, owners, consumidores, contratos e evidências. Inventariar GLPI real (inventário nativo, GLPI Agent e plugins), Zabbix/monitoramento existente, integrações no monorepo e eventual solução de gestão de endpoints. Registrar `EXISTING_EQUIVALENT` e `REUSE_DECISION` por fonte.
- Confirmar abrangência, unidades, endereços permitidos, sistemas Windows/Linux, disponibilidade de agentes ou WinRM/SSH, permissões somente leitura, cadência e restrições operacionais.
- Confirmar fabricante/modelo, firmware SFOS e plano de gerenciamento do Sophos; selecionar **conforme disponibilidade comprovada** API local REST (quando suportada), API XML legada, API Sophos Central e/ou SNMPv3. Inventariar endpoints e campos efetivamente disponíveis antes de prometer DHCP, VPN ou outras informações em tempo real.
- Definir ownership por atributo, identificadores estáveis e correlação com os cadastros E1/E2A/E2B. IP isolado não é identidade permanente. Observações automáticas devem ter origem, horário, confiança e ciclo de vida; divergência cria candidato/revisão, não substituição silenciosa.
- Fixar contratos de conectores e sincronização: apenas leitura da origem, segredo em vault/config protegida, escopo de rede restrito, rate limits, timeouts, auditoria, reprocessamento idempotente, observabilidade, falha parcial e retorno seguro. Não executar varreduras indiscriminadas, comandos remotos privilegiados, alteração do Sophos ou exclusão automática de ativos.

**Ordem de investigação/entrega proposta, sujeita aos gates:** (1) inventário de fontes e piloto limitado; (2) coleta Windows/Linux por mecanismo já disponível ou adaptador read-only aprovado; (3) coleta do Sophos compatível com a versão; (4) normalização, reconciliação com inventário existente e agendamento; (5) UI mostrando origem, última coleta, divergências e aprovação dos candidatos.

**Fora do escopo da E4 inicial:** mapas da E3A, simulação da E3B, detecção/alertas contínuos da futura observabilidade, escrita remota/configuração do firewall, descoberta ativa irrestrita e importação de credenciais ou payloads sensíveis.

## E4.S1 — piloto automático Linux srv-api (execução autorizada, implantação condicionada)

**Estado:** READY_TO_EXECUTE no escopo do produto, **NOT_IMPLEMENTED**. Autorização do PO em 10/11/2026 para avançar com o piloto. Código, configuração Keycloak, execução agendada e validação em produção ainda exigem suas evidências próprias. O executor não se autoaceita.

**BASE_HEAD de planejamento:** `025728aadaab626083247d410cab0be47f3cf226` (reancorar novamente antes de editar). **Owner:** `it-portal-api` para contratos e dados de observações; `plugins/it-portal` para visualização; executor de infraestrutura para coleta local Linux agendada. Core/Keycloak continuam owners de identidade/autorização.

**Inventário provado:** `srv-api` Ubuntu 24.04.4 LTS em VMware; 16 vCPUs, ~23 GiB RAM, storage raiz ~197 GiB, rede principal `192.168.1.237/24`; ~114 containers Docker no momento da coleta; Zabbix Agent 2 7.0.23 ativo (hostname/memória disponíveis, chave CPU inconclusiva). Disco raiz ~83% utilizado, swap ~100% na amostra. Nada disso comprova integração automática.

**Reuso antes de invenção:**
- `EXISTING_EQUIVALENT = TO_INVENTORY` para transportes de observações/coletores reutilizáveis; pesquisar e abrir fontes canônicas antes de criar.
- `REUSE_DECISION = EXTEND` a API, tabelas e UI existentes do Portal de TI; `REUSE` autenticação S2S canônica `shared/delpi_auth/service_token_{provider,validator}.py` quando aplicável. Não criar identidade nem token paralelo. Leitura local Linux via ferramentas do SO; Zabbix opcional somente quando a chave e o ownership forem comprovados.
- `GLPI` não é dependência: computadores/endpoints fora do escopo. Sophos, Windows, E3A/E3B também não entram no piloto Linux.

**Contrato-alvo a aprovar antes do código de ingestão:**
- Snapshot estruturado **somente leitura** do host: hostname, identidade estável protegida, SO/kernel, CPU, RAM/swap, volumes, interfaces físicas, serviços e resumo dos containers (quando permitido). Nunca coletar env, volumes sensíveis, argumentos de processo, tokens, senhas, mounts detalhados/segredos ou stdout indiscriminado. Limites de cardinalidade e timeout por comando; sem root e sem acesso irrestrito ao socket Docker.
- Observação persistida distinta de campos manuais do servidor: `source`, `observed_at`, `received_at`, `server_id`, `run_id` idempotente, `schema_version`, `status` e resumo validado; reter histórico finito. Servidor pré-existente é correlacionado pelo ID e identidade estável; IP isolado não prova identidade. Nunca criar/arquivar/alterar servidor manualmente sem aprovação.
- **S2S:** interfaces humanas atuais do Portal de TI exigem `principal_type=user`. Um coletor não pode usar token de usuário, superadmin, header forjado nem endpoint público desprotegido. Avaliar contrato e implementação isolados para identidade técnica Keycloak client-credentials, audience, allowed client e escopo de ingestão, fail-closed, com testes negativos. Se a adequação do middleware violar o boundary, `ARCHITECTURE_DECISION_REQUIRED` e STOP na ingestão.
- Preview/dry-run local antes de registrar snapshots; API deve autorizar a origem da observação e conferir binding com servidor alvo. Sem segredos em logs; sem registro direto em banco externo. Agendamento desligado até smoke controlado. 
- UI de detalhe do servidor com origem e horário da coleta, saúde/status, resumo técnico, diferenças e estados vazio/erro/desatualizado, respeitando `servers.view`; aceitar alterações de campos manuais só em operação explícita e autorizada.

**Aceite esperado:** testes unitários do coletor e domínio; Postgres real com migration aditiva e idempotência; contrato HTTP, S2S (401/403/503 e cliente/scope indevidos), histórico e autenticação humana inalterados; frontend testes + build + visual; ensaio read-only no `srv-api` comprovando ausência de regressão operacional; ativação agendada e outcome de coleta periódica somente após gate operacional. Reportar `PASS|FAIL|PENDING|TEST_NOT_RUN` por aceite, diff, SHA, comando e evidência de runtime. Não marcar COMPLETE só por commit/testes.

## Residuais abertos

| ID | Residual | Dono da decisão |
|---|---|---|
| RES-GLPI-01 | Definir se registros vivos do GLPI (DatabaseInstance, Appliance, IPNetwork) passam a ser authority para algum cadastro do Portal de TI | PO |
| RES-OPENAPI-01 | `/openapi.json`, `/docs` e `/redoc` são públicos (contrato, sem dados do inventário) | PO / segurança |
