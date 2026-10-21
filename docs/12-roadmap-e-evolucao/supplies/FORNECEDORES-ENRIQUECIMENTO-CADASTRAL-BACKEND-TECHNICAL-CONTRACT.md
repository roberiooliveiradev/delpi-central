# Backend technical contract — enriquecimento cadastral assistido de fornecedores

> **Status: PROPOSED CONTRACT / TARGET; NOT IMPLEMENTED; NOT FROZEN.** Complementa [fluxo/RQ](./FORNECEDORES-ENRIQUECIMENTO-CADASTRAL-FLUXO-CONTRATO.md) e [UX](./FORNECEDORES-ENRIQUECIMENTO-CADASTRAL-FRONTEND-UX-CONTRACT.md). O PO pediu especificação técnica, **não autorizou código, migration, consultas externas de CNPJ, jobs, deploy ou PUT**. Schemas, paths, estados e SQL abaixo são **desenho alvo**, não fatos sobre o HEAD. Após inventory de runtime e aprovação de G0–G5, preparar OpenAPI canônico e migration executável. Não declarar este desenho frozen sem resolver decisões do §15.

## 1. Contexto / fronteira

**Escopo assumido:** fornecedores TOTVS **SA2** do Portal Suprimentos. A expressão "clientes cadastrados" usada no pedido original pode significar SA1; se confirmado, abrir bounded context próprio e **STOP/EXECUTION_DRIFT**.

```text
MFE plugins/supplies
  → supplies-api (Flask): Core effective AuthZ, review/decisions, audit, orchestration
       ↘ api-delpi: read canonical SA2, contract/PUT/tracking (separados)
       ↘ official/authorized CNPJ provider via owned adapter HTTP
  → (future, explicit confirmation) supplies-api → api-delpi → Protheus REST MATA020
```

Antes de escolher adapter CNPJ, procurar owner corporativo existente. Contrato genérico corporativo pode morar em serviço compartilhado, sem mover regras de comparação/decisão do Portal. **Consulta CEP recentemente centralizada na api-delpi não autoriza inferir que CNPJ siga o mesmo owner.** Keycloak identidade; Core permission final; JWT não é permissions. `supplies-api` nunca consulta SQL TOTVS; não espelhar SA2 no Postgres `supplies`.

## 2. Responsabilidades Ports & Adapters

| Layer | Componente TARGET | Responsabilidade |
|---|---|---|
| domain | `EnrichmentReview`, `FieldProposal`, `FieldDecision`, `SourceEvidence`, `ReviewStatus` | invariantes de snapshot, decisões, elegibilidade |
| application | `CreateSupplierEnrichmentReview` | autorizar, carregar SA2 e fonte oficial, validar identidade, comparar e versionar |
| application | `GetSupplierEnrichmentReview` | recuperar revisão em escopo e com redaction |
| application | `DecideSupplierEnrichmentField` | decisão individual idempotente e auditável |
| application | `DecideSupplierEnrichmentBulk` | decisão em lote transacional e previsível |
| application | `PrepareSupplierEnrichmentUpdate` | revalidar baseline/allowlist e preparar diff sem PUT |
| application | `ListSupplierEnrichmentHistory` | recuperar eventos mínimos autorizados |
| ports | `SupplierCanonicalReader` | GET canonical SA2 via api-delpi |
| ports | `CompanyRegistryProvider` | consulta estruturada de CNPJ, com proveniência |
| ports | `EnrichmentReviewRepository`, `EnrichmentEventWriter` | estado próprio e auditoria de domínio |
| adapters | HTTP, CoreAuthz, api-delpi gateway, provider, Postgres | sem imports de domain alheio |
| UX | `plugins/supplies` | render comparação e decisões; nunca fonte de AuthZ |

**Não criar novo serviço ou processo agendado no MVP.** O estado durável proposto abaixo torna as recusas auditáveis, mas precisa de aceite da política LGPD, retenção e migration antes de implementação.

## 3. Segurança e identidade (gate por requisição)

- `supplier_access = capability AND unit_scope AND resource_scope/ownership AND business_rule`; resolver permissão efetiva no Core; negar em falha.
- Operações de leitura e decisão são distintas da operação de PUT: decisão não equivale a escrita em ERP. Usar capability de fornecedor vigente apenas **se a semântica contratada a abranger**, sem permissão por campo/tela/CRUD. Caso o acesso à decisão exija capability adicional, decidir em contrato Core, não inventar claim JWT.
- JWT autenticado identifica `actor_subject`; context, unit e resource são validados server-side a cada request. Todas as rotas de review e histórico checam `supplier_code/store`, contexto/unit e ID de revisão, impedindo IDOR.
- CNPJ usado na fonte externa precisa pertencer ao fornecedor SA2 autorizado. Não aceitar CNPJ arbitrário em request de review. Não expor CPF a consulta de CNPJ.
- Provider HTTP com host allowlisted, TLS, timeout, rate limit, quotas, não redirecionar a host arbitrário, sanitização, cache particionado quando aprovado, PII minimizada.
- Logs técnicos contêm apenas `correlation_id`, `review_id`, actor pseudonimizado e contagens/status, nunca CNPJ completo, token ou resposta integral.

## 4. HTTP contract v0 — prefixo supplies-api

**Endpoints TARGET, nenhum implementado.** Base: `/apps/supplies-api`; schemas propostos para posterior incorporação ao OpenAPI canônico.

| Método | Rota | Sucesso | Erros principais |
|---|---|---|---|
| POST | `/suppliers/{code}/{store}/enrichment-reviews` | 201 review pronta, 202 apenas se async explicitamente aprovado | 400/401/403/404/409/422/429/502/503/504 |
| GET | `/suppliers/{code}/{store}/enrichment-reviews/{review_id}` | 200 review | 401/403/404/410 |
| GET | `/suppliers/{code}/{store}/enrichment-reviews` | 200 histórico paginado | 401/403/404/422 |
| POST | `/suppliers/{code}/{store}/enrichment-reviews/{review_id}/decisions` | 200 review atualizado | 401/403/404/409/410/422 |
| POST | `/suppliers/{code}/{store}/enrichment-reviews/{review_id}/bulk-decisions` | 200 review atualizado; tudo-or-nada dentro do snapshot | 401/403/404/409/410/422 |
| POST | `/suppliers/{code}/{store}/enrichment-reviews/{review_id}/prepare-update` | 200 preview tipado **sem escrita ERP** | 401/403/404/409/410/422 |
| PUT | rota existente de edição de fornecedor | resultado do contrato PUT atual | gates/authorization/tracking atuais, sem novo caminho |

**Escolha:** POST create-review síncrono no MVP se SLA do provider suportar; timeout devolve erro sem review pronta. Não prometer 202 nem polling até aprovar orchestration async.

### Create review request

```json
{ "source_preference": "default" }
```

O cliente **não informa CNPJ, permissões, campo editável, fonte arbitrária, baseline, unidade ou URL**. Source preference é candidata, default server-side; remover parâmetro se só uma fonte autorizada.

### Create/get review response (contrato candidato)

```json
{
  "review_id": "opaque-review-id",
  "supplier": {"code":"000001","store":"01"},
  "status": "AWAITING_DECISIONS",
  "revision": 1,
  "expires_at": "2026-10-22T12:00:00Z",
  "source": {
    "provider": "approved-source",
    "retrieved_at": "2026-10-21T12:00:00Z",
    "coverage": "partial",
    "reference_version": null
  },
  "summary": {"total_compared": 5,"different": 2,"eligible_pending": 1,"protected": 1,"not_comparable": 1},
  "fields": [{
    "field_key":"district",
    "section_key":"address",
    "current_display":"CENTRO",
    "suggested_display":"CENTRO NOVO",
    "comparison":"DIFFERENT",
    "eligibility":"ELIGIBLE_TO_APPLY",
    "decision":"PENDING",
    "reason":null,
    "source_field":"address.district",
    "confidence":"source_reported"
  }],
  "can_prepare_update": true
}
```

**Exemplo fictício**; server-side `baseline_fingerprint` e `source_fingerprint` podem ser substituídos por `revision`/ETag assinado, **não transmitir hashes de CNPJ ou PII reversíveis** sem revisão. `current_display` e `suggested_display` são valores reduzidos para UI; backend mantém valores tipados autorizados somente pelo TTL aprovado, protegidos criptograficamente se persistidos.

### Decision request individual

```json
{
  "field_key": "district",
  "decision": "ACCEPT",
  "expected_revision": 1,
  "idempotency_key": "client-generated-opaque-uuid",
  "reason_code": null
}
```

- `ACCEPT` → `ACCEPTED_FOR_DRAFT`; `REJECT` → `REJECTED_SUGGESTION`; ambos não chamam PUT.
- Campo fora do snapshot, protegido ou não elegível → 422/409 conforme motivo; chave/idempotency duplicada com payload diferente → 409.
- Responder com novo `revision`, contagens atualizadas e os campos afetados; evitar depender de state do cliente para autorização.

### Bulk decision request

```json
{
  "decision": "REJECT",
  "expected_revision": 3,
  "idempotency_key": "client-generated-opaque-uuid",
  "field_keys": ["district", "postal_code"]
}
```

- Lista explícita precisa coincidir com os campos elegíveis **PENDING do snapshot no momento do preview**, sob revision esperada. Backend recalcula; itens protegidos ou já decididos → 409/422, não ignorar silenciosamente.
- **Atomicidade proposta:** uma transação para toda a decisão em lote, sem partial commit. Se provider SQL/Postgres/infra falhar, rollback local. Chamada de ERP nunca ocorre nessa transação.
- Repetição da mesma idempotency key + mesmo payload retorna resultado consistente sem evento duplicado.

### Prepare-update request/response

```json
{ "expected_revision": 4 }
```

Resposta: `{review_id, revision, supplier, draft_fields:[{field_key,current_display,proposed_display}], excluded_fields, baseline_status:"CURRENT", write_gate_enabled:false, requires_final_confirmation:true}` (conceitual). `write_gate_enabled` é apenas informação UX; autorização e gate serão rechecados no PUT de verdade. Preparação **não executa PUT**. Se SA2 alterou desde snapshot: `409 STALE_BASELINE`, exigindo nova revisão.

### Error envelope (alinhamento obrigatório ao padrão do BFF)

```json
{
  "error": {
    "code": "ENRICHMENT_REVIEW_STALE",
    "message": "Os dados foram alterados. Consulte novamente antes de aplicar.",
    "correlation_id": "opaque-correlation"
  }
}
```

O envelope acima é **proposto**: usar estrutura de erros existente na supplies-api se diferente. Códigos candidatos: `SUPPLIER_NOT_FOUND`, `ENRICHMENT_UNSUPPORTED_DOCUMENT`, `ENRICHMENT_SOURCE_UNAVAILABLE`, `ENRICHMENT_IDENTITY_MISMATCH`, `ENRICHMENT_REVIEW_EXPIRED`, `ENRICHMENT_REVISION_CONFLICT`, `ENRICHMENT_NOT_ELIGIBLE`, `ENRICHMENT_RATE_LIMITED`, `ENRICHMENT_STALE_BASELINE`.

## 5. Máquina de estados e transições

**Review:** `REQUESTED → FETCHED → COMPARED → AWAITING_DECISIONS → DECIDED`, terminando `CANCELLED` ou `EXPIRED`. Falhas: `SOURCE_ERROR`, `IDENTITY_MISMATCH`, `STALE_BASELINE`. Os estados REQUESTED/FETCHED/COMPARED são efêmeros no desenho síncrono; **não precisam ser gravados como steps de job**. `DECIDED` significa que todas as sugestões elegíveis já foram decididas, não que ERP recebeu update.

**Field:** `PENDING → ACCEPTED_FOR_DRAFT | REJECTED_SUGGESTION`. Revisão/reversão por nova decisão **só se política de reverter estiver aprovada**; MVP recomenda decisão irreversível no snapshot, exigindo nova revisão para reconsiderar, até PO definir.

**Write:** fluxo de PUT/operation-tracking existente, separado. Nenhum estado de review usa `CONFIRMED` como equivalente a persistência ERP.

Transições só podem ocorrer com review não expirada, revision atual, actor autorizado e campo elegível.

## 6. Comparação, elegibilidade e normalização

**Matriz conservadora inicial:**
- **PROTECTED:** CNPJ/CPF, código, loja, identidade, atributos fiscais protegidos.
- **POTENTIALLY_COMPARABLE:** razão social, fantasia (sem presumir equivalência com A2_NREDUZ), endereço (validar número/complemento e SX3), bairro, CEP, cidade/UF (CC2), telefone/e-mail (fonte e qualidade).
- **INFORMATION_ONLY:** CNAE/situação da empresa, sem mapeamento PUT canônico.
- **INTERNAL_NOT_FROM_PROVIDER:** condições de pagamento, natureza financeira, conta contábil, banking etc.

**FieldComparison**: `MATCH|DIFFERENT|SOURCE_MISSING|CURRENT_MISSING|NOT_COMPARABLE|PROTECTED|UNSUPPORTED|ERROR`; **Eligibility**: `ELIGIBLE_TO_APPLY|PROTECTED|NOT_APPLICABLE|PENDING_VALIDATION`. Não equiparar DIFFERENT a elegível. Não propor clears quando fonte é nula/vazia. Normalizar sem ocultar diferenças semânticas; preservar texto exato para revisão (e limites físicos). Nome fantasia de fonte pode divergir de abreviação interna; regra de equivalência pendente.

**Dependências:** `state + city + city_code` podem precisar ser grupo indivisível após conciliação UF+CC2; modelar `dependency_group` no campo, e recusar aceitar subset inválido. CEP/endereço podem precisar regra de consistência, não copiar IBGE externo diretamente para A2_COD_MUN.

## 7. Modelo de dados alvo (Postgres supplies, não espelho SA2)

**Subject to migration review, privacy approval and authority.** Modelo lógico, sem SQL executável nesta documentação.

```text
supplier_enrichment_reviews
  id UUID PK
  supplier_code VARCHAR(..), supplier_store VARCHAR(..)
  unit_scope_id / resource_scope ref (canônico, validar owner)
  actor_subject UUID, provider_id VARCHAR
  status ENUM/string, revision INT, created_at, expires_at, last_consulted_at
  baseline_fingerprint BYTEA (HMAC server secret, NOT plain hash CNPJ)
  source_fingerprint BYTEA (HMAC)
  source_coverage, correlation_id, metadata_redacted
  unique logical scope as approved; indexes expires_at, resource+created_at

supplier_enrichment_proposals
  id UUID PK, review_id FK
  field_key VARCHAR allowlisted, section_key VARCHAR
  comparison_state, eligibility_state, eligibility_reason
  current_value_encrypted? / proposed_value_encrypted? (if storage authorized)
  current_display_redacted? / proposed_display_redacted?
  source_field, confidence, normalization_version, dependency_group
  unique(review_id, field_key)

supplier_enrichment_decisions
  id UUID PK, review_id FK, proposal_id FK
  actor_subject UUID, decision, reason_code, decision_version, decided_at
  idempotency_key UUID, request_fingerprint HMAC
  unique(review_id, idempotency_key); compound constraint per field/revision if approved

supplier_enrichment_events (append-only)
  id UUID PK, review_id FK, actor_subject UUID
  event_type, at, correlation_id, minimal_metadata_redacted
  index(review_id, at)
```

**Modeling rules:** stable UUIDs; no SA2 replica, no external bulk blob by default; client never writes audit event directly. Encrypt sensitive proposed values at rest if persisted, strict service access, short TTL and cleanup job **only if job approved**; audit events may outlive snapshots with minimal non-PII metadata. Snapshot expiration and audit retention need explicit DPO/owner decision. If durability not approved, fallback to **ephemeral signed review** with inability to promise durable cross-session refusals; **do not falsely document persistent decisions**.

**Invariant database:** decision transaction uses row lock/optimistic revision; per-review atomic bulk; unique idempotency keys, referential integrity; no SQL to SA2. Field labels/keys from allowlist, no dynamic column writes.

## 8. Integration adapters and error semantics

**Canonical supplier reader**: `supplies-api` calls existing `api-delpi` through gateway authorized; obtains current SA2 snapshot. `NOT_FOUND` distinct from insufficient field projection. GET may not return all fields; if current absent because projection incomplete, classify `NOT_COMPARABLE`, **do not assume empty ERP field**.

**CNPJ provider**: do not choose without inventory. Candidate official services/data sources need provider URL, auth, legal basis, license, schema, freshness, rate policy and fallback policy proven. National CNPJ digits and branch identity validated; data source not trusted as authoritative for internal business fields. Provider can return partial; per-field provenance required.

**Rate/cache**: timeout bounded; per-user/unit/CNPJ quotas; optional TTL cache only for an approved scope, with separation by authorization; no background polling in MVP.

**Failures:**
- Provider 404/empty ≠ SA2 supplier absent.
- Provider 429 → `ENRICHMENT_RATE_LIMITED`, honor approved cooldown.
- Provider 5xx/timeout → 502/504, no `SOURCE_MISSING` for all fields.
- Identity mismatch → 409/422 blocked; never compare to different entity.
- Partial external response → review with unavailable fields (no blind overwrite).
- Core unavailable → deny/503 fail-closed.
- Existing supplier changes → 409 stale on prepare and prior to PUT.
- Write gate OFF → review and decisions may remain available, but saving disabled.
- Tracking ACK/UNKNOWN post-write → outcome-specific UX, no automatic retry.

## 9. Observability/audit contract

Log `request_id, correlation_id, review_id, actor_subject (access controlled), provider_id, supplier scoped reference, counts, status transitions, latencies`; never raw CNPJ/CPF, address, contacts, tokens or full provider payload in ordinary logs. Business audit events append-only, with result and decision reason but no plaintext sensitive value. Consumer access auditing separated from Core platform audit, and from `api-delpi.integration_tracking` which is only for forwarded writes.

Retention, erasure, incident access, data classification, encryption and source licensing require privacy gate. No generic index exposing snapshots across units.

## 10. Tests and executable proofs required at implementation

| Group | Required tests |
|---|---|
| AuthZ | positive actor/unit/resource, sibling unit/resource 403/404, unauthenticated 401, Core down fail-closed |
| Sources | provider success/partial/empty, bad CNPJ, wrong CNPJ, 429/5xx/timeout, schema changes, provenance |
| Comparison | MATCH/different/unknown, missing vs blank, protected, unsupported, no clear, normalizations, SX3 limits, dependent fields |
| Decisions | accept/reject individual, pending-only bulk, noneligible injection, reason, atomicity, duplicate idempotency, same-key different payload 409 |
| Concurrency | optimistic revision race, baseline changed since consultation, expiry, replay, cross-review IDOR |
| Persistence | migration reversible, FK/unique/index, transaction rollback, retention, encryption/no plaintext logs |
| Write separation | accept/reject no PUT, prepare-update no PUT, gate OFF, PUT-only confirmed via api-delpi and tracking, UNKNOWN no retry |
| UX integration | schema parity with UX contract, 403/404/409/410/429/5xx, no auto-write |
| Runtime | server authenticated GET/POST tests with fixtures, federated smoke, screenshots, SHAs/rollback; if not run INCONCLUSIVE |

Minimum proof for every AC: baseline HEAD, exact files, RQ/AC mapping, contract source, positive/sibling/negative, test commands/results, sanitization checks, residual search. Never interpret test existence as runtime proof.

## 11. Rollout plan — future only

`S0` provider/legal/owner inventory → `S1` contract freeze (schemas + mappings + policies) → `S2` backend domain/repositories/migration with security review → `S3` read-only compare source and canonical ERP → `S4` decision API/atomic bulk → `S5` MFE pages and Help → `S6` runtime smoke read-only → `S7` optional apply-draft integration with existing PUT under independent write gate. Do not treat approval of S0 as authorization for S7.

Deployment when authorized: backend compatible before MFE; no altered ERP endpoint, no changes in Protheus gates, rollback by image and migration-compatible strategy. No PROD write during initial inventory or contract freeze.

## 12. Explicit non-goals

- Bulk scanning all suppliers, scheduled jobs, automated changes, unsolicited periodic comparisons.
- Client SA1 records, commercial module, customer enrichment.
- CPF enrichment, protected-tax-id rewrite, banking/financial external overwrite.
- General CNPJ shared service until a company-wide owner/contract is proven.
- New permissions for every action, table, field or UI button.
- Bypassing existing PUT contract and write tracking.
- Treating source API as more authoritative than SA2.

## 13. RQ/AC contract mapping

| Backend AC | Acceptance |
|---|---|
| BE-AC-01 | Supplier snapshot loaded only via api-delpi owner |
| BE-AC-02 | Source provider contract and legal/access policy proven |
| BE-AC-03 | Identity/CNPJ match before suggestions |
| BE-AC-04 | No personal data beyond approved coverage persisted |
| BE-AC-05 | Comparison respects limits, source missing, protected and dependencies |
| BE-AC-06 | Review auth resource/unit fail-closed |
| BE-AC-07 | Idempotent individual decisions and revision |
| BE-AC-08 | Atomic bulk only pending+eligible with preview |
| BE-AC-09 | Rejected suggestions never trigger ERP write |
| BE-AC-10 | Accepted suggestions only prepared as draft |
| BE-AC-11 | Baseline drift blocks prepare/write |
| BE-AC-12 | No new PUT path or bypass of tracking |
| BE-AC-13 | Expiration/retention and privacy policy enforced |
| BE-AC-14 | S2S/provider gateway security and sanitized logs |
| BE-AC-15 | API schemas and errors align with BFF/UX |
| BE-AC-16 | Positive/sibling/negative and runtime smoke evidenced |
| BE-AC-17 | No background jobs or auto-write in MVP |
| BE-AC-18 | Docs/Help/SHAs and rollback documented |

## 14. Decisions needed for freeze / questions to PO, security, owner

| ID | Open decision | Recommended default | Status |
|---|---|---|---|
| B-01 | Review state persisted? | Yes, minimal; refuse durably; subject LGPD/retention | PENDING |
| B-02 | Review TTL? | short, configurable (example 24h) | PENDING |
| B-03 | Retention of audit events? | DPO-approved period, separate from review TTL | PENDING |
| B-04 | Individual decisions reversible? | New review to reconsider, no silent overwrite | PENDING |
| B-05 | Bulk conflict policy? | Atomic, pending-only, expected_revision | PROPOSED |
| B-06 | Provider CNPJ official? | Inventory first, no URL assumed | PENDING |
| B-07 | Provider source field mapping? | Contract/provenance per field before eligibility | PENDING |
| B-08 | Write integration? | Existing PUT only; future separate gate/GO | PROPOSED |
| B-09 | Review visibility? | Resource-scoped, audit view role by Core | PENDING |
| B-10 | Audit consent/legal/retention? | Security/LGPD review required | PENDING |
| B-11 | CNPJ on non-J entities? | unsupported by default | PROPOSED |
| B-12 | List/history retention and pagination defaults? | bounded, indexes, no bulk export | PENDING |

**Freeze prerequisites:** exact HEAD inventory; provider verified and licensed; source/SA2 mapping verified; Core scope model; storage/privacy policy; atomicity, TTL, durable audit and response schemas approved; OpenAPI integration owner; test matrix; explicit feature GO. **Failure on a prerequisite → `TO_INVENTORY` or `EXECUTION_DRIFT`, never silently implement.**

## 15. Formal classification

`BACKEND_CONTRACT = PROPOSED / TARGET`  
`GATE_PROVIDER = TO_INVENTORY`  
`GATE_PRIVACY = PENDING`  
`GATE_MAPPING = TO_INVENTORY`  
`GATE_DECISION_POLICY = PENDING`  
`IMPLEMENTATION = NOT_AUTHORIZED`  
`NO_SCHEMA_CHANGE / NO_ENDPOINT / NO_PROVIDER_CALL / NO_DEPLOY`
