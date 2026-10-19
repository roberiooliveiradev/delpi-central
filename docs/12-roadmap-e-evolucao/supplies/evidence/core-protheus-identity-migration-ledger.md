# Ledger — migração identidade Protheus → Core API

| Campo | Valor |
|-------|--------|
| TASK | Core Protheus identity ownership + cutover hardening |
| SHA base revisão | `095f3f0bb22cf92518e0cf075a6fd1a0fc73cd92` |
| SHA implementação original | `0bab7c315c` |
| Chamado | #1354 (não encerrado automaticamente) |
| `EXISTING_EQUIVALENT` | `NO` |
| `REUSE_DECISION` | `EXTEND` |
| Código hardening / `origin/main` | `5896fc568b433e5ab95e18234fccfd3fc8e6ddb1` |
| `PRODUCTION_CUTOVER` | `PENDING` |
| Data migração produção | não executada nesta rodada |

## Correções desta rodada (review independente)

| Problema | Correção |
|----------|----------|
| Script podia escrever antes de falhar por conflitos | Gate fail-closed: plano → bloqueio → só então apply transacional |
| Órfãos ignorados | `orphan_user` / `inactive_user` blocking |
| `--allow-conflicts` | removido |
| Overwrite cego no destino | divergência Core = conflito; idêntico = no-op |
| `list_mappings()` legado no modo core | S2S list paginado + facade Core; sem fallback legado |
| S2S PUT sem caller/ator | allowlist `X-Delpi-Caller-App` + `actor_user_id` validado + audit |

## Testes (evidência)

| Suíte | Resultado |
|-------|-----------|
| Core `test_protheus_identity` + `test_migrate_protheus_identities_script` | **20 passed** (container `delpi-core-api`) |
| SC `test_protheus_identity_owner_facade` + sync | **8 passed** |

## Operação produção

| Etapa | Status |
|-------|--------|
| Deploy código hardening | PENDING (após merge `main`) |
| Backup Core + plugins mappings | PENDING (autorização operacional) |
| Inventário somente leitura | PENDING |
| Dry-run script | PENDING |
| Apply + reconciliação | PENDING |
| `PROTHEUS_IDENTITY_OWNER=core` efetivo | PENDING |
| Smoke Portal/SC/API DELPI | PENDING |

## Classificação (estado factual)

| Dimensão | Status |
|----------|--------|
| CODE_CORRECTIONS | PASS (código local; SHA final após push) |
| MIGRATION_SCRIPT | PASS (testes de planner) |
| SCHEMA_PRODUCTION | PENDING |
| PRODUCTION_DEPLOYMENT | PENDING |
| DATA_INVENTORY | PENDING |
| DATA_MIGRATION | PENDING |
| DATA_RECONCILIATION | PENDING |
| CORE_OWNERSHIP | PENDING (flag ainda `legacy` até cutover) |
| PORTAL_SMOKE | TEST_NOT_RUN (prod) |
| PURCHASE_REQUESTS_SMOKE | TEST_NOT_RUN (prod) |
| S2S_SECURITY | PASS (testes unitários deny/allow) |
| DOCUMENTATION | PASS |
| BUSINESS_OUTCOME | PENDING |
