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

**Objetivo da E4 (PLANNED):** minimizar o cadastro manual de servidores Windows/Linux e da infraestrutura de rede Sophos, sem criar uma segunda autoridade sobre ativos existentes, nem sobrescrever dados operacionais curados por pessoas.

**Gate inicial (TO_INVENTORY), antes de aprovar contratos/implementação:**

- Reancorar em GitHub HEAD, regras, owners, consumidores, contratos e evidências. Inventariar GLPI real (inventário nativo, GLPI Agent e plugins), Zabbix/monitoramento existente, integrações no monorepo e eventual solução de gestão de endpoints. Registrar `EXISTING_EQUIVALENT` e `REUSE_DECISION` por fonte.
- Confirmar abrangência, unidades, endereços permitidos, sistemas Windows/Linux, disponibilidade de agentes ou WinRM/SSH, permissões somente leitura, cadência e restrições operacionais.
- Confirmar fabricante/modelo, firmware SFOS e plano de gerenciamento do Sophos; selecionar **conforme disponibilidade comprovada** API local REST (quando suportada), API XML legada, API Sophos Central e/ou SNMPv3. Inventariar endpoints e campos efetivamente disponíveis antes de prometer DHCP, VPN ou outras informações em tempo real.
- Definir ownership por atributo, identificadores estáveis e correlação com os cadastros E1/E2A/E2B. IP isolado não é identidade permanente. Observações automáticas devem ter origem, horário, confiança e ciclo de vida; divergência cria candidato/revisão, não substituição silenciosa.
- Fixar contratos de conectores e sincronização: apenas leitura da origem, segredo em vault/config protegida, escopo de rede restrito, rate limits, timeouts, auditoria, reprocessamento idempotente, observabilidade, falha parcial e retorno seguro. Não executar varreduras indiscriminadas, comandos remotos privilegiados, alteração do Sophos ou exclusão automática de ativos.

**Ordem de investigação/entrega proposta, sujeita aos gates:** (1) inventário de fontes e piloto limitado; (2) coleta Windows/Linux por mecanismo já disponível ou adaptador read-only aprovado; (3) coleta do Sophos compatível com a versão; (4) normalização, reconciliação com inventário existente e agendamento; (5) UI mostrando origem, última coleta, divergências e aprovação dos candidatos.

**Fora do escopo da E4 inicial:** mapas da E3A, simulação da E3B, detecção/alertas contínuos da futura observabilidade, escrita remota/configuração do firewall, descoberta ativa irrestrita e importação de credenciais ou payloads sensíveis.

## Residuais abertos

| ID | Residual | Dono da decisão |
|---|---|---|
| RES-GLPI-01 | Definir se registros vivos do GLPI (DatabaseInstance, Appliance, IPNetwork) passam a ser authority para algum cadastro do Portal de TI | PO |
| RES-OPENAPI-01 | `/openapi.json`, `/docs` e `/redoc` são públicos (contrato, sem dados do inventário) | PO / segurança |
