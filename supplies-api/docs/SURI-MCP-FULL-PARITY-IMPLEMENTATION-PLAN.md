# SURI-MCP-FULL-PARITY-IMPLEMENTATION-PLAN — Roadmap executável

Task: `SURI-MCP-FULL-PARITY-P0` · HEAD `8a822e29c1` · Autorização: planejamento apenas — nenhum lote executa sem aceite próprio.
Objetivo do programa: `SURI_AUTHORIZED_PORTAL_PARITY = 100%`.

## Princípios (preservados em todos os lotes)

```text
5 tools hoje (rev.3) → 6 tools alvo: get_context, read, analyze, knowledge, execute, delete
Closed (entity, action) registry — nunca executor universal, URL, SQL ou handler arbitrário
Bearer do usuário end-to-end (paridade com BFF) — S2S gateway quando o BFF usa S2S
Policies canônicas supriladas por chamada (mesmas do Flask) — nunca permissão paralela
DELETE → confirmação explícita sempre; CREATE/UPDATE não-destrutivos → direct quando inequívocos
PREPARE→proposal→commit quando houver risco/ambiguidade/regra obrigatória (padrão CLARA/EVA)
Idempotency key por operação · resultado individual em batch · read-back pós-write
Nenhuma operação bloqueada no Portal pode existir na SURI
Schemas MCP evoluem aditivamente (novos Literals/entities) — compatibilidade com conector já publicado
```

## Ordem e dependências

```text
FASE P1 — READ/ANALYZE parity (capacidades já homologadas no Portal)
  P1-R1 purchase_requests (EXECUTADO — SURI-MCP-FULL-PARITY-V4-G2, catálogo v5)
  → P1-R2 PO export (EXECUTADO — V4-G2) → P1-R3 deliveries+inventory
  → P1-R4 safety_stock → P1-R5 suppliers reads (EXECUTADO —
    SURI-MCP-FULL-PARITY-V4-G1, catálogo v4) → P1-R6 analytics
  → P1-R7 consumption_audit → P1-R8 market_intelligence → P1-R9 users/me/home
  → P1-A1 analyze por entidade → P1-K1 corpus knowledge
FASE P2 — EXECUTE/DELETE parity (só writes plugin-db/workflow homologadas)
  P2-E0 supplier create/update ERP (EXECUTADO — SURI-MCP-SUPPLIERS-WRITE-001)
  → P2-E1 fundação governed-write (registry+proposal+idempotency+audit)
  → P2-E2 comex (views CRUD + ncm request/transition) → P2-E3 enrichment
  → P2-E4 preferences/profile → P2-D1 delete (views)
FASE P3 — BLOCKED (não agenda): SC workflow (supplier writes saíram de P3 em 2026-10-30)
FASE P4 — TARGET: páginas ainda não implementadas no próprio Portal
```

Cada lote é independente em código (novo `entity`/`action` no registry + handlers + schemas + testes) mas dependente de P1-* anteriores apenas por convenção de catálogo (`SEMANTIC_CAPABILITIES`/`catalog_version` bump sequencial).

## Lotes (resumo; briefs completos em SURI-MCP-FULL-PARITY-EXECUTION-BRIEFS.md)

| Lote | TASK | Entrega | Files prováveis | Stop conditions |
|---|---|---|---|---|
| P1-R1 | SURIP-R1: `read entity=purchase_requests` | **EXECUTADO** — search/summary/requesters/cost_centers/get/export (catálogo v5, TESTED_LOCALLY) | `tool_bridge.py`, `schemas.py`, `constants.py`, `PurchaseRequestsGateway` + `RequesterIdentityService` reuse, `test_purchase_requests_read.py` | facets guard quebrar; units deny errado |
| P1-R2 | SURIP-R2: PO export | **EXECUTADO** — export = dataset JSON+meta do mesmo upstream `/supplies/purchase-orders/export` (TESTED_LOCALLY) | `tool_bridge.py`, `constants.py`, `schemas.py`, tests | artefato sem parity com BFF export |
| P1-R3 | SURIP-R3: deliveries + inventory | `read entity=deliveries` (late), `read entity=inventory` (summary/items) | tool_bridge + SuppliesDelpiReads reuse | N/A |
| P1-R4 | SURIP-R4: safety_stock | filters/summary/items/details/suppliers | tool_bridge | `all` branch vazar sem choice → retornar erro estruturado |
| P1-R5 | SURIP-R5: suppliers reads | list/get/catalogs/postal-code/dup-check/preview/integration-status(manage)/operations | tool_bridge + **DelpiS2SApiGateway** | integration-status sem manage → 403 correto (negative test) |
| P1-R6 | SURIP-R6: analytics | `analyze analysis=overview_summary`, `read entity=otd` (aggregate+series) | tool_bridge + OverviewCompositionService reuse | fan-out parcial → honest partial |
| P1-R7 | SURIP-R7: consumption_audit | orders search/get/comparison | tool_bridge + S2S gateway | audience/scope upstream 403 repassar corretamente |
| P1-R8 | SURIP-R8: market_intelligence | filters/summary/series×5/quotes+compare/monthly-avg + comex products + governance/views reads | tool_bridge + MarketIntelligenceService/ComexAnalysisService | provider `unavailable`/`source_use_pending` → estado honesto, nunca sintético |
| P1-R9 | SURIP-R9: users/me/home | user profile/related/photo (self\|manage), me/preferences read, home attention counts | tool_bridge + UserProfileService + count sources | profile de outro usuário sem manage → 403 |
| P1-A1 | SURIP-A1: analyze multi-entidade | `purchase_requests_summary`, `suppliers_summary`, `consumption_audit_summary`, `safety_stock_summary`, `market_intelligence_summary` | analyze registry + facts determinísticos + input_hash | analyze sem dados → recommendations honestas |
| P1-K1 | SURIP-K1: corpus ampliado | entradas knowledge por nova entidade/ação | `app/content/suri_knowledge.json` + version bump | hash/version integrity test |
| P2-E1 | SURIP-E1: governed-write foundation | capability registry ACT, proposal store (pg `supplies` ou in-process HMAC EVA-style — DECISION), prepare→commit, idempotency store, audit `mcp/suri`, `execute`/`delete` tool registration, `delpi/toolClass=PREPARE/ACT` | new `app/application/suri/` + `mcp/act_*` + pg migration opcional | sem consent channel verificável p/ ops obrigatórias → confirmation_unavailable honest |
| P2-E2 | SURIP-E2: comex execute/delete | `execute` comex.view.save + ncm.request + transition(manage→consent); `delete` comex.view | capability entries + reuse ComexAnalysisService | transition manage sem manage → 403; ED-api put falha → partial honest |
| P2-E3 | SURIP-E3: enrichment execute | review.create, decide, bulk-decide, prepare-update | reuse SupplierEnrichmentReviewService (expected_revision/idempotency já embutidos) | rate-limit actor → 429 honest |
| P2-E4 | SURIP-E4: preferences execute | `execute` me.preferences.update + user.profile.update (self) | reuse PreferencesService | write de outro usuário → 403 |
| P2-D1 | SURIP-D1: delete foundation + views | `delete` tool + confirmation obrigatória (target_echo elicit OU consent url — DECISION P2-E1) + read-back gone | tool + policy | client sem elicit/consent → confirmation_unavailable 403 |
| P2-E0 | SURI-MCP-SUPPLIERS-WRITE-001: supplier create/update ERP | **EXECUTADO** — `execute` rev.3 (W-10/W-11) | `supplier_execute.py`, `tool_bridge.py`, `schemas.py`, `constants.py`, `server.py`, `suppliers_dto.py` (classifier compartilhado), `delpi_api_gateway.py` (X-Correlation-ID), 30 testes | gates OFF em runtime → write_disabled honest (nunca executar) |
| P3-* | BLOCKED | SC workflow | — | NÃO IMPLEMENTAR até B-03 desbloquear |
| P4-* | TARGET | my-tasks/products/negotiations/indicators/administration | — | depende do Portal implementar primeiro |

## Gates por lote (template comum)

```text
G1 contract: Literals/schemas fechados, extra=forbid, catalog_version bump
G2 dispatch: handler especializado, bearer forward, policy check por call
G3 tests: positive + sibling + negative + authz denials + contract frozen tests
G4 regressão: suíte supplies-api inteira + suri_mcp verde
G5 evidence: tools/list retorna surface esperada; JSON-RPC real initialize/list/call
G6 doc: matrix row → PROVEN; evidence doc por lote
```

## Decisões abertas (a fechar no primeiro lote que as toca)

1. **DECISION-E1**: proposal store — Postgres `supplies` schema (CLARA-style, auditável cross-restart) vs HMAC in-process (EVA-style, single-process). Recomendo **pg** pela consistência com proposals persistentes e audit.
   **Subdecisão fechada no P2-E0 (2026-10-30):** para writes não-destrutivas sem exigência de consent/prepare (supplier create/update — direct path, sem prepare/commit conversacional redundante conforme contrato da missão), a infra mínima é: registry `(entity,action)` fechado + replay cache in-process de `idempotency_key` (TTL 900s, guarda de retry, não fonte de verdade) + operation tracking durável do api-delpi (`operation_id`, `X-Correlation-ID` propagado) + audit estruturado por operação. O proposal store pg continua DECISION aberta para operações que exijam consent/prepare (enrichment, comex manage, delete).
2. **DECISION-D1**: canal de confirmação — MCP elicitation `target_echo` (EVA) vs Portal consent url (CLARA). Recomendo **elicitation com echo** (MCP-native, sem dependência de UI nova) com fallback `confirmation_unavailable` honesto.
3. **DECISION-G1** — **FECHADA (V4-G2):** export via MCP = dataset JSON filtrado canônico + metadados do artefato (`format`, `row_count`, `portal_file_formats`). Sem binário/base64/link arbitrário — materialização CSV/XLSX permanece exclusiva das rotas BFF. Motivo: o contrato MCP corrente não tem canal de artefato homologado (sem resource/download endpoint próprio); dataset JSON é o menor mecanismo compatível com o recorte autorizado do Portal e com a UX do conector (o LLM consome as linhas diretamente).
4. `patchPreferences` vs `patchUserProfile` — reconciliar owner da write (TO_INVENTORY).

## Compatibilidade OAuth / conector

Adição de tools é non-breaking para OAuth (audience/scopes inalterados); conector ChatGPT continua funcionando entre releases — `tools/list` simplesmente ganha itens. Mudanças em `read`/`analyze` são aditivas (novos valores de Literal), preservando calls existentes.
