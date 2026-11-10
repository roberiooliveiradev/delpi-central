# it-portal-api — BFF do Portal de TI

API própria do Portal de TI (Minha DELPI). Única origem de dados do MFE
`plugins/it-portal`; não consulta a api-delpi nem bancos de outros produtos.

- **Base pública:** `/apps/it-portal-api` (gateway → `it-portal-api:8000`)
- **OpenAPI:** `GET /openapi.json` (operationIds estáveis, `bearerAuth` em todas as rotas exceto `/health`)
- **Persistência:** postgres-plugins, schema isolado `it_portal`
  (`IT_PORTAL_DB_*`, com fallback para `PLUGINS_DB_*`)
- **Migrations:** `migrations/V*.sql`, aplicadas no startup quando
  `IT_PORTAL_RUN_MIGRATIONS_ON_STARTUP=true`; checksum SHA-256 registrado e
  advisory lock. Migration aplicada é imutável — mudança de schema = novo `V00N`.

## Camadas

```text
domain/          regras puras (validação, catálogos, transições, guarda de segredos)
application/     serviços (servidores, notas, planos, dashboard, serviços, bancos,
                 redes, integrações) + ports
infrastructure/  PostgresItPortalRepository, PostgresInventoryRepository,
                 PostgresConnectivityRepository, migrations runner
interface/http/  rotas FastAPI, schemas Pydantic, authz
```

## Inventário de serviços e bancos (E2A — `V002`)

| Entidade | Tabela | Observações |
|---|---|---|
| Serviço / aplicação (`SVC-0001`) | `services` | `service_kind` separa aplicação de negócio de serviço de plataforma; nome único ativo por unidade + ambiente |
| Instância em execução | `service_hostings` | vínculo serviço → servidor com `runtime` (container, processo, serviço do SO…); par único |
| Instância de banco (`DB-0001`) | `database_instances` | servidor hospedeiro obrigatório; nome único ativo por servidor; **sem credenciais** |
| Consumo de banco | `database_consumers` | vínculo serviço → instância; par único |

- Vínculos são removidos com `DELETE` (somente a associação; FKs `RESTRICT`
  impedem apagar cadastros). Criação e remoção são auditadas com snapshot dos
  dois lados.
- `audit_events.subject_ids` lista todos os recursos afetados; o histórico de
  servidor, serviço e banco é `entity_id = X OR subject_ids @> [X]`.
- Cadastro arquivado é somente leitura e não recebe novos vínculos (409).
- Nenhum dado é semeado. A API não se conecta aos bancos inventariados.

## Redes, integrações e relacionamentos (E2B — `V003`)

| Entidade | Tabela | Observações |
|---|---|---|
| Rede (`NET-0001`) | `networks` | CIDR validado/normalizado no backend (exige prefixo e endereço de rede); VLAN 1–4094; gateway dentro do CIDR; `network_scope` explícito (`corporate` × `container_runtime`); nome único ativo por unidade; CIDR único ativo por unidade só para redes corporativas |
| Conectividade | `server_network_links` | vínculo servidor → rede; IP opcional precisa pertencer ao CIDR (revalidado sob lock); par único; alterar o CIDR com IPs vinculados fora dele → 409 `network_links_outside_cidr` |
| Integração (`INT-0001`) | `integrations` | cada ponta é **um** serviço cadastrado **ou** um sistema externo nomeado (não cadastrado); pelo menos uma ponta interna; sem autointegração; única ativa por origem + destino + protocolo; **sem credenciais/payloads** |
| Dependência operacional | `service_dependencies` | dependente → requerido, explícita (nunca presumida); sem autodependência; par único |

Tipos de relacionamento e onde vivem:

| Tipo | Tabela(s) |
|---|---|
| hospedagem | `service_hostings`, `database_instances.server_id` |
| consumo | `database_consumers`, `integrations` |
| conectividade | `server_network_links` |
| dependência operacional | `service_dependencies` |

- Consulta por recurso: `/servers/{id}/network-links`, `/servers/{id}/integrations`
  (integrações dos serviços hospedados), `/networks/{id}/server-links`,
  `/services/{id}/integrations`, `/services/{id}/dependencies`.
- Sem varredura de rede, discovery, agentes ou integração automática
  GLPI/Zabbix. Mapa interativo e análise de impacto ficam para a Etapa 3.

## Autorização

Toda rota (exceto `/health`) exige JWT Keycloak válido **e** RBAC efetivo do
Core (`shared/delpi_auth`). JWT válido sozinho não autoriza; RBAC indisponível
responde 503. Apenas principals humanos (`principal_type=user`).

| Permissão | Concede |
|---|---|
| `it-portal.access` | abrir o portal (`/me/capabilities`) |
| `it-portal.servers.view` | inventário, detalhe, notas, histórico, dashboard |
| `it-portal.servers.manage` | cadastrar, editar, arquivar, restaurar (com `servers.view`) |
| `it-portal.notes.create` | registrar notas (com `servers.view`) |
| `it-portal.actions.view` | listar/consultar planos (com `servers.view`) |
| `it-portal.actions.manage` | criar, editar, alterar status (com `servers.view`) |
| `it-portal.services.view` | listar/consultar serviços e onde executam (com `servers.view`) |
| `it-portal.services.manage` | CRUD/arquivo de serviços, vincular/desvincular servidores (com `servers.view` + `services.view`) |
| `it-portal.databases.view` | listar/consultar instâncias de banco (com `servers.view`) |
| `it-portal.databases.manage` | CRUD/arquivo de instâncias (com `servers.view` + `databases.view`) |
| `it-portal.networks.view` | listar/consultar redes e a conectividade servidor ↔ rede (com `servers.view`) |
| `it-portal.networks.manage` | CRUD/arquivo de redes, conectar/desconectar servidores (com `servers.view` + `networks.view`) |
| `it-portal.integrations.view` | listar/consultar integrações (com `servers.view` + `services.view`) |
| `it-portal.integrations.manage` | CRUD/arquivo de integrações (com as permissões de leitura) |

Dependências operacionais pertencem ao domínio de serviços: leitura com
`servers.view` + `services.view`, escrita com `services.manage`.

Listar ou alterar vínculos serviço ↔ banco exige ver os **dois** lados
(`services.view` + `databases.view`), além do `manage` de bancos para escrever.

Toda escrita revalida as permissões no Core sem cache nem fallback stale
(`authorize_write` → `load_user_rbac(force_refresh=True)`): permissão
revogada não grava, e Core indisponível nesse lookup responde 503 sem gravar.
Leituras usam o RBAC com cache do middleware.

Escritas gravam o evento de auditoria (`audit_events`) na mesma transação,
com o autor real do token. Logs de acesso registram só rota, operationId,
status e duração — nunca payload de inventário.

## Testes

```bash
python -m pytest -q
# integração com Postgres real (banco descartável por módulo):
IT_PORTAL_TEST_DSN=postgresql://user@host:5432/postgres python -m pytest -q
```
