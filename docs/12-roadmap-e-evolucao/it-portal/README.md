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

**Estado:** IMPLEMENTED_PENDING_SMOKE — código/V004/S2S ingest/UI/coletor/provisioner Keycloak `--check` entregues; COMPLETE só após smoke real (diagnose + observação visível com S2S provisionado). Agendamento systemd permanece desabilitado. Apply Keycloak e timer = gates operacionais separados. O executor não se autoaceita.

**BASE_HEAD de planejamento:** `025728aadaab626083247d410cab0be47f3cf226` (superado; reancorar no HEAD do commit E4.S1). **Owner:** `it-portal-api` para contratos e dados de observações; `plugins/it-portal` para visualização; executor de infraestrutura para coleta local Linux agendada. Core/Keycloak continuam owners de identidade/autorização.

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

## Revisão independente E4.S1 — 11/11/2026

**REVIEW_DECISION: ACCEPT_WITH_RESIDUAL** para o artefato de código `1884eddf34bcbc796f1e9f525e8ee6cbdd07ea5b`. **Estado operacional: IMPLEMENTED_PENDING_SMOKE; não é COMPLETE.** Inspeção estática no GitHub; sem acesso ao runtime do `srv-api` e sem reprodução local dos testes apresentados pelo executor. A `main` avançou somente em frente externa após a entrega na data da revisão.

**PASS reportado pelo executor:** testes API sem Postgres, frontend 82/82, arquitetura/gates e CLI `diagnose` parcial esperado. **TEST_NOT_RUN / PENDING:** Postgres real V004 (não demonstrado), deploy, V004 aplicada em produção, client credentials Keycloak, allowlist do UUID do `srv-api`, `submit` autêntico, leitura humana da observação no MFE e timer desabilitado.

**Residuais/gates antes da ativação do S2S:**
1. `it_portal_app/domain/observations.py::_sanitize_summary` filtra nomes sensíveis no nível superior, mas preserva chaves aninhadas desconhecidas no JSON. `ObservationIngestInput.summary` é `dict` livre; o repositório grava esse resultado no JSONB. Restringir recursivamente ao contrato de campos aceitos ou rejeitar estruturas desconhecidas/sensíveis, com testes adversariais. **Não habilitar ingresso S2S de produção antes desse ajuste delimitado e nova revisão.**
2. `collectors/linux_host/submit.py` importa `delpi_auth.service_token_provider`, que importa `requests`. O comando divulgado `PYTHONPATH=it-portal-api python3 -m collectors.linux_host submit` não garante dependências nem `shared` disponíveis no Python do host. Verificar o ambiente e prover execução isolada/reprodutível; evitar `pip` global e scripts com credenciais em argumentos. O `systemd` usa `/opt/delpi/it-portal-collector`, usuário próprio e env em `/etc/delpi`; instalação/venv/permissões não foram comprovadas.
3. O provisioner `--apply` é operação de administração Keycloak e escreve segredo em `infra/.env`; executar primeiro `--check` e validar endpoint HTTPS, controle de arquivo e impacto da mudança. O arquivo de env do coletor é distinto e **não** é carregado automaticamente pelo comando CLI interativo.
4. Implantação inicial da API + MFE pode ocorrer **com S2S_ALLOWED_CLIENTS e allowlist vazios** (fail-closed), em ordem API primeiro, MFE depois. Verificar saúde, versionamento API `0.4.0`, V004, render vazio/compatibilidade e ausência de regressões. Após o gate acima, provisionar identidade técnica aprovada e comprovar `diagnose`→`submit`→GET humano→UI. **Não habilitar timer** até autorização operacional separada.

**Critério de fechamento:** smoke com resultado material e verificável em produção, dados manuais preservados, nenhum segredo coletado, identidade vinculada ao cadastro e observação com `run_id` idempotente. Se houver divergência de owner/security, registrar `EXECUTION_DRIFT` / `ARCHITECTURE_DECISION_REQUIRED`, sem improvisar bypass.

## E4.S1 — smoke diagnóstico completo no srv-api (11/11/2026)

**Evidência reportada pelo operador (PROVEN pela saída do terminal fornecida no chat, sem log remoto independente):**
- `python3 -m collectors.linux_host diagnose` executado com Python em ambiente virtual isolado no próprio `srv-api`.
- `status: complete`, com as sete seções `identity`, `os`, `memory`, `volumes`, `nics`, `systemd` e `docker` retornando `ok`.
- Superado o erro local de dependências `ModuleNotFoundError: No module named 'jose'` com ambiente de execução isolado; a instalação systemd de produção, serviço/usuário próprio e acesso ao ambiente de coleta permanecem **PENDING**.
- A API 0.4.0 foi identificada em container no `srv-api` na evidência anterior; não há ainda prova de V004 aplicada por consulta de banco, `submit` S2S, observação persistida, apresentação no Portal nem agendamento.
- **GATE AINDA ABERTO:** corrigir/validar sanitização estrita de campos JSON aninhados no resumo de observações antes de habilitar S2S de ingestão, conforme revisão anterior. `submit`, Keycloak `--apply` e timer continuam **PENDING**.

**Estado:** `IMPLEMENTED_PENDING_SMOKE`, mesmo após o diagnóstico local `PASS`. A E4.S1 só recebe aceite completo após envio autenticado, persistência, visualização, controles de segurança e decisão de agendamento respaldados por evidência.

## E4.S1 — diagnóstico do Keycloak --check no host (11/11/2026)

**Evidência operacional (saída enviada pelo operador):**
- No `srv-api` host, `python3 infra/scripts/keycloak_s2s_it_portal_collector.py --check` escolheu `base=http://keycloak:8080/auth` (nome de serviço resolvido apenas na rede Docker apropriada). A emissão do token de consulta falhou em `socket.getaddrinfo` com `Temporary failure in name resolution`, antes de verificar se o cliente `it-portal-host-collector` existe.
- **Diagnóstico:** não há evidência de Keycloak indisponível nem de cliente inexistente. Resultado `CHECK = INCONCLUSIVE` por conectividade host → nome Docker. Nenhuma configuração foi aplicada.
- `systemctl is-enabled it-portal-linux-collector.timer` retornou `not-found`: unidade systemd não instalada no host; agendamento **não ativo**. Não interpretar como `disabled`.
- **Próximo gate somente leitura:** identificar um `KC_BASE_URL` HTTPS alcançável pelo host, preferencialmente URL corporativa válida, sem vazar segredos; executar `KC_BASE_URL=... python3 infra/scripts/keycloak_s2s_it_portal_collector.py --check`. Se for inacessível, investigar topologia/entrypoint sem modificar DNS ou abrir acesso administrativo desnecessário.
- Permanecem bloqueados `--apply`, `submit` e ativação do timer até saneamento do contrato de ingestão JSON e revisão dos gates de segurança anteriormente registrados.

## E4.S1 — Keycloak check por HTTPS (11/11/2026)

**Evidência operacional (saída enviada pelo operador, PROVEN na execução reportada):**
- `curl -fsS https://minhadelpi.com.br/auth/realms/delpi/.well-known/openid-configuration` respondeu `issuer=https://minhadelpi.com.br/auth/realms/delpi`. Keycloak público e realm `delpi` acessíveis via HTTPS a partir do host; não comprova acesso a todas as operações internas.
- `KC_BASE_URL=https://minhadelpi.com.br/auth python3 infra/scripts/keycloak_s2s_it_portal_collector.py --check` executou a leitura administrativa e informou `[DRIFT] client it-portal-host-collector — inexistente`. O cliente técnico do piloto ainda exige provisionamento aprovado; o check não cria nem altera recursos.
- O operador estava autenticado como `michael`, com repositório em `/home/operador/projetos/delpi-central`. O `cd ~/projetos/delpi-central` falhou por apontar para `/home/michael`, mas a consulta seguinte executou no CWD anterior e produziu resposta. Runbooks devem usar caminho absoluto/descoberto.
- A `infra/.env` contém `KEYCLOAK_ADMIN_URL=http://keycloak:8080` (nome de serviço Docker, não resolvível diretamente no host), `KEYCLOAK_ISSUER=${PUBLIC_BASE_URL}/auth/realms/${KEYCLOAK_REALM}` e `KC_HOSTNAME=http://localhost:9080/auth`; esses valores exigem análise contextual de runtime antes de qualquer mudança. **Não alterar o Keycloak para resolver o piloto**, pois o issuer público está validado.
- `--apply`, `submit` e timer **não autorizados neste gate**. O bloqueio de sanitização estrita recursiva no payload JSON de observações continua válido e precisa de correção, testes e revisão antes de abrir ingestão S2S.
- Próxima verificação segura: confirmar V004 em `it_portal.schema_migrations` e identidade do servidor registrado no Portal de TI via consulta SQL somente leitura no container da API, sem publicar credenciais.

**Estado:** `IMPLEMENTED_PENDING_SMOKE`. `Keycloak CHECK=PASS_COM_DRIFT_CLIENT_MISSING`, `S2S PROVISIONING=PENDING`, `OBSERVATION SUBMIT=PENDING`.

## E4.S1 — verificação de migration e identidade do srv-api (11/11/2026)

**Evidência observada no `srv-api` (consulta SQL somente leitura executada pelo operador no container `delpi-it-portal-api`):**
- `it_portal.schema_migrations` registra `version=4`, `name=V004__server_observations.sql` (**PASS**: migration V004 aplicada; a consulta não demonstrou contagem de linhas ou grants da tabela).
- Cadastro alvo na tabela `it_portal.servers`: `id=459fd1b8-643f-493d-9911-0ff7aaf91424`, `hostname=srv-api`, `active=true` (**PASS**: registro existente e elegível para conciliação por hostname).
- Não há necessidade de criar outro cadastro do `srv-api`; preservar campos manuais.
- **PENDING (antes desta correção de segurança):** sanitização/allowlist de payload JSON em profundidade, provisionamento Keycloak S2S, configuração segregada do coletor, smoke `submit` autenticado com `run_id`, leitura humana no MFE e agendamento systemd. `COMPLETE` continua pendente.

## E4.S1 — gate de segurança: allowlist estrita do summary (11/11/2026)

**Causa raiz (CONFIRMADO_NO_CODIGO):** `_sanitize_summary` usava denylist só no nível superior e preservava chaves desconhecidas dentro de objetos/listas aninhadas (`os`, `memory`, `docker_summary`, etc.), permitindo persistência JSONB de campos fora do contrato do coletor.

**Correção (owner `it-portal-api/it_portal_app/domain/observations.py`):**
- allowlist de seções/campos alinhada ao coletor Linux v1;
- varredura recursiva rejeita chaves sensíveis (`password`, `token`, `secret`, `env`, `credentials`, `authorization`, `private_key`, etc.);
- campos desconhecidos não sensíveis são descartados; limites de tamanho/cardinalidade preservados;
- `sections_status` restrito às seções do coletor.

**Evidência de testes (local, antes do commit desta fatia):**
- `pytest tests/test_observations_domain.py tests/test_observations_http.py tests/test_http_contract.py` → PASS (positivo com snapshot realista + negativos aninhados parametrizados).
- Sem alteração de V004, cadastro manual, escopos S2S, Keycloak `--apply`, `submit` ou timer.

**Estado após esta fatia:** residual de sanitização aninhada **ATENDIDO_NO_CODIGO** (sujeito a revisão independente). Demais gates S2S/smoke/timer permanecem **PENDING**. `COMPLETE` não declarado.

## E4.S1 — primeiro submit S2S bloqueado pela borda HTTP (11/11/2026)

**Evidência reportada pelo operador:**
- A execução manual no `srv-api` completou a validação local (`VALIDACAO: PASS`) e as sete seções do coletor (`COLETA: complete`), com `run_id=c603a7a4-f088-4209-9bcd-fb9ffd907134`.
- O `submit` para `https://minhadelpi.com.br/apps/it-portal-api` retornou `HTTP 403`, corpo literal `error code: 1010\n`. Esse código é atribuído pela documentação Cloudflare ao bloqueio de assinatura do cliente HTTP. **CAUSA PROVÁVEL**: camada web pública rejeitando o cliente `urllib`; **sem evidência** de rejeição do token pelo validador S2S da API.
- Não presumir gravação ou ausência de gravação a partir de `HTTP 403` isoladamente. **PENDING** consulta somente leitura em `it_portal.server_observations` por esse `run_id`.
- O Compose vigente publica `delpi-gateway` em `80:80` e o Nginx encaminha `/apps/it-portal-api/` para `it-portal-api:8000` (prefixo removido). **TARGET para investigação**: testar `http://127.0.0.1/apps/it-portal-api/health` com `Host: minhadelpi.com.br`, sem credenciais, antes de tentar um único `submit` interno com autenticação S2S inalterada.
- Não desativar Cloudflare/WAF, não expor novas portas, não colocar secrets em logs ou argumentos, não mudar Keycloak, não habilitar timer; primeiro smoke produtivo e visualização no MFE continuam `PENDING`.
- Provisionamento Keycloak e allowlists na API foram reportados pelo operador como funcionais em passos anteriores, mas ainda carecem de read-back independente nesta ocorrência.

**Status:** `IMPLEMENTED_PENDING_SMOKE`; falha inicial classificada como `BLOCKED_AT_PUBLIC_EDGE` até prova adicional. Chamada do GLPI #1571 deve permanecer aberta.

## Residuais abertos

| ID | Residual | Dono da decisão |
|---|---|---|
| RES-GLPI-01 | Definir se registros vivos do GLPI (DatabaseInstance, Appliance, IPNetwork) passam a ser authority para algum cadastro do Portal de TI | PO |
| RES-OPENAPI-01 | `/openapi.json`, `/docs` e `/redoc` são públicos (contrato, sem dados do inventário) | PO / segurança |
