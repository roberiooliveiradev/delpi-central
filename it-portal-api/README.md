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
application/     serviços (servidores, notas, planos, dashboard, serviços, bancos) + ports
infrastructure/  PostgresItPortalRepository, PostgresInventoryRepository, migrations runner
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

## Autorização

Toda rota (exceto `/health`) exige JWT Keycloak válido **e** RBAC efetivo do
Core (`shared/delpi_auth`). JWT válido sozinho não autoriza; RBAC indisponível
responde 503. Apenas principals humanos (`principal_type=user`).

| Permissão | Concede |
|---|---|
| `it-portal.access` | abrir o portal (`/me/capabilities`) |
| `it-portal.servers.view` | inventário, detalhe, notas, histórico, dashboard |
| `it-portal.servers.manage` | cadastrar, editar, arquivar, restaurar |
| `it-portal.notes.create` | registrar notas (com `servers.view`) |
| `it-portal.actions.view` | listar/consultar planos (com `servers.view`) |
| `it-portal.actions.manage` | criar, editar, alterar status (com `servers.view`) |
| `it-portal.services.view` | listar/consultar serviços e onde executam (com `servers.view`) |
| `it-portal.services.manage` | CRUD/arquivo de serviços, vincular/desvincular servidores (com `servers.view` + `services.view`) |
| `it-portal.databases.view` | listar/consultar instâncias de banco (com `servers.view`) |
| `it-portal.databases.manage` | CRUD/arquivo de instâncias (com `servers.view` + `databases.view`) |

Listar ou alterar vínculos serviço ↔ banco exige ver os **dois** lados
(`services.view` + `databases.view`), além do `manage` de bancos para escrever.

Escritas gravam o evento de auditoria (`audit_events`) na mesma transação,
com o autor real do token. Logs de acesso registram só rota, operationId,
status e duração — nunca payload de inventário.

## Testes

```bash
python -m pytest -q
# integração com Postgres real (banco descartável por módulo):
IT_PORTAL_TEST_DSN=postgresql://user@host:5432/postgres python -m pytest -q
```
