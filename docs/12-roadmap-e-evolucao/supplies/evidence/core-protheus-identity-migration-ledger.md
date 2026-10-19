# Ledger — migração identidade Protheus → Core API

| Campo | Valor |
|-------|--------|
| TASK | Core Protheus identity ownership |
| SHA base | `8fc45e2119f3cc7b1b34a0f79bca144e5f822516` (`origin/main` no reanchor) |
| SHA final `main` | `0bab7c315c1dcc3edddd4b1675e9994d8a0e6c51` |
| Branch | `feat/core-protheus-identity` (rebased → merged via FF push to `main`) |
| `EXISTING_EQUIVALENT` | `NO` |
| `REUSE_DECISION` | `EXTEND` |
| Código | `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW` |
| `PRODUCTION_CUTOVER` | `PENDING` |
| Data migração produção | não executada (proibido sem autorização) |
| Schema local (dev) | `flask db upgrade` → `t6u7v8w9x0` (head) aplicado em `delpi-core-api` |
| Testes Core | `pytest app/tests/test_protheus_identity.py` → **11 passed** |
| Testes SC | facade + sync + notification preference → **7 passed** |

## Matriz de consumidores (inventário)

| Consumidor | Contrato anterior | Destino |
|---|---|---|
| Portal Admin aba TOTVS | purchase-requests `/rbac/user-protheus-mappings` | Core `/admin/rbac/users/.../external-identities/protheus` |
| SC sync-by-email | SC use case + repo local | Repo facade → Core quando `PROTHEUS_IDENTITY_OWNER=core` |
| SC notificações reverse lookup | `get_mapping_by_protheus_user_id` local | Idem via Core S2S |
| SC admin PUT mappings | local writer | Facade → Core no cutover |
| API DELPI SYS_USR | `/supplies/protheus-users/by-email` | **inalterado** (adapter) |

## Resultados de classificação

| Dimensão | Status |
|----------|--------|
| CORE_IDENTITY_CAPABILITY | PASS (código) |
| SCHEMA_MIGRATION | PASS (Alembic criada; apply em runtime) |
| DATA_MIGRATION | PENDING (script dry-run; prod não aplicada) |
| PORTAL_CONSUMER | PASS (aba TOTVS → Core) |
| PURCHASE_REQUESTS_CONSUMER | PASS (facade + flag cutover) |
| S2S_SECURITY | PASS (token integrations) |
| REGRESSION_TESTS | ver evidência de execução |
| DOCUMENTATION | PASS |
| PRODUCTION_CUTOVER | PENDING |
