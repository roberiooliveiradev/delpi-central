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
application/     serviços (servidores, notas, planos, dashboard) + ports
infrastructure/  PostgresItPortalRepository, migrations runner
interface/http/  rotas FastAPI, schemas Pydantic, authz
```

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

Escritas gravam o evento de auditoria (`audit_events`) na mesma transação,
com o autor real do token. Logs de acesso registram só rota, operationId,
status e duração — nunca payload de inventário.

## Testes

```bash
python -m pytest -q
# integração com Postgres real (banco descartável por módulo):
IT_PORTAL_TEST_DSN=postgresql://user@host:5432/postgres python -m pytest -q
```
