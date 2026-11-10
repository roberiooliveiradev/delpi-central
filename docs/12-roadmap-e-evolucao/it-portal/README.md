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
| E3 | Mapa interativo e análise de impacto | — | fora do escopo atual | — |

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

## Residuais abertos

| ID | Residual | Dono da decisão |
|---|---|---|
| RES-GLPI-01 | Definir se registros vivos do GLPI (DatabaseInstance, Appliance, IPNetwork) passam a ser authority para algum cadastro do Portal de TI | PO |
| RES-OPENAPI-01 | `/openapi.json`, `/docs` e `/redoc` são públicos (contrato, sem dados do inventário) | PO / segurança |
