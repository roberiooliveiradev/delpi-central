# Supplier Enrichment — Review & Decision API (S2)

> **Status: IMPLEMENTED (S2).** Persistência de revisões, propostas por campo,
> decisões individuais/em lote e prepare-update draft na `supplies-api`.
> Reutiliza o domain/comparison engine de S1
> (`supplier-enrichment-comparison-domain.md`).

## Boundaries

- Dono: `supplies-api` (review domain + estado + AuthZ server-side + persistência própria).
- Canonical read: `api-delpi` `GET /integrations/protheus/suppliers/{id}` (read-only, S2S existente).
- **Fonte externa configurável (S3.1)**: `COMPANY_REGISTRY_PROVIDER=unavailable` (default) mantém `UnavailableCompanyRegistryProvider` fail-closed → `503 ENRICHMENT_SOURCE_UNAVAILABLE`. `=brasilapi` habilita `BrasilApiCompanyRegistryProvider` (`provider_id=brasilapi-cnpj-v1`, conceitual `THIRD_PARTY_API`, nunca `GOVERNMENT_API`) — consulta sob demanda server-side, allowlist de campos, sem QSA/CPF, rate limit por ator e por CNPJ.
- **Zero escrita ERP**: nenhum endpoint emite POST/PUT Protheus; `prepare-update` produz somente draft.
- Navegador **não** declara: `actor_subject`, `unit_context`, `source_id`, `source_reference`, `review_id`, `created_at`, `status`, `revision`, snapshots externos → 422 `invalid_request`.

## AuthZ — SUPPLIER_RESOURCE_SCOPE_CONTRACT (GATE-A)

```text
capability (supplies.access via Core /me)
AND resource_scope (review.actor_subject == current_user.id)
AND business_rule (person_type J + CNPJ identity + review window)
```

- `unit_scope` para fornecedores é **inexistente na plataforma** (SA2 = master data global; Core `/me` não emite unidades por usuário) — ausência documentada em
  `supplier-enrichment-resource-scope-contract.md`; `unit_context` permanece `NULL`.
- Revisão é propriedade do ator criador (fail-closed; compartilhamento é contrato futuro).
- Core indisponível → 503 (middleware fail-closed existente).

## Rotas

| Método | Path | operationId |
|---|---|---|
| POST | `/suppliers/<code>/<store>/enrichment-reviews` | `create_supplier_enrichment_review` |
| GET | `/suppliers/<code>/<store>/enrichment-reviews` | `list_supplier_enrichment_reviews` |
| GET | `…/enrichment-reviews/<review_id>` | `get_supplier_enrichment_review` |
| GET | `…/enrichment-reviews/<review_id>/decisions` | `list_supplier_enrichment_decisions` |
| POST | `…/enrichment-reviews/<review_id>/decisions` | `decide_supplier_enrichment_field` |
| POST | `…/enrichment-reviews/<review_id>/bulk-decisions` | `decide_supplier_enrichment_fields_bulk` |
| POST | `…/enrichment-reviews/<review_id>/prepare-update` | `prepare_supplier_enrichment_update` |

Envelope de erro: `{"detail": …, "code": …}` (padrão existente do BFF).

## Máquina de estados da revisão

```text
IN_REVIEW ──(todas as propostas decididas)──▶ DECIDED
IN_REVIEW ──(expires_at decorrido, lazy)────▶ EXPIRED
IN_REVIEW/DECIDED ──(baseline drift no prepare)──▶ STALE
CANCELLED — reservado (sem transição em S2)
```

Decisões exigem `IN_REVIEW|DECIDED`? Não — apenas `IN_REVIEW`. Estados
actionables: `IN_REVIEW` e `DECIDED` permanece legível; decisões em review
`EXPIRED`/`STALE`/`CANCELLED` → 410/409.

## Idempotência e concorrência

- `idempotency_key` obrigatória (1–128 chars), única por revisão. Replay com
  o **mesmo payload** (hash canônico) → `idempotent_replay: true` sem escrita;
  payload divergente → `409 ENRICHMENT_IDEMPOTENCY_CONFLICT`.
- `expected_revision` obrigatório — otimista: `UPDATE … WHERE revision = expected`
  na mesma transação das decisões; divergência → `409 ENRICHMENT_REVISION_CONFLICT`.
- Bulk: todas as `field_keys` são validadas (existência, pendência,
  elegibilidade para ACCEPT) antes de qualquer escrita — atômico.
- REJECT é permitido em proposta pendente mesmo não elegível; ACCEPT exige
  `ELIGIBLE_TO_APPLY` + spec `COMPARABLE` (tax_id/identidade/informativos
  nunca são aceitos — verificação dupla no draft).

## Erros explícitos

| Condição | HTTP | code |
|---|---|---|
| sem token / token inválido | 401 | `unauthorized` |
| sem capability / outro ator | 403 | `forbidden` |
| supplier/review/proposal inexistente | 404 | `not_found` |
| provider externo ausente | 503 | `ENRICHMENT_SOURCE_UNAVAILABLE` |
| CNPJ inexistente no provider | 404 | `ENRICHMENT_REGISTRY_TAX_ID_NOT_FOUND` |
| CNPJ não numérico / rejeitado | 422 | `ENRICHMENT_REGISTRY_INVALID_TAX_ID` |
| cap de consultas (ator/CNPJ/429 provider) | 429 | `ENRICHMENT_RATE_LIMITED` (+`Retry-After`) |
| resposta inválida/divergente do provider | 502 | `ENRICHMENT_REGISTRY_INVALID_RESPONSE` |
| revisão expirada | 410 | `ENRICHMENT_REVIEW_EXPIRED` |
| baseline divergente | 409 | `ENRICHMENT_STALE_BASELINE` |
| revisão cancelada | 409 | `ENRICHMENT_REVIEW_CANCELLED` |
| revision divergente | 409 | `ENRICHMENT_REVISION_CONFLICT` |
| idempotency reusada c/ payload divergente | 409 | `ENRICHMENT_IDEMPOTENCY_CONFLICT` |
| proposta já decidida | 409 | `ENRICHMENT_PROPOSAL_ALREADY_DECIDED` |
| ACCEPT em não elegível / CPF | 422 | `ENRICHMENT_PROPOSAL_NOT_ELIGIBLE` / `ENRICHMENT_UNSUPPORTED_DOCUMENT` |
| body inválido / campos server-owned | 422 | `invalid_request` |

## Persistência (V002 + V003)

`supplies.supplier_enrichment_{reviews,proposals,decisions,events}` +
`supplier_enrichment_decision_operations` — UUIDs server-side, FK RESTRICT,
`UNIQUE(review_id, field_key)`, revision otimista, eventos append-only,
timestamps UTC. `tax_id` nunca é persistido em proposta (valores `NULL`).

**V003 (rework):** a identidade da requisição idempotente vive em
`decision_operations` — `UNIQUE(review_id, idempotency_key)`,
`request_hash`, `review_revision`, `decision`, `reason_code`. Cada
`decision` por campo referencia `operation_id NOT NULL`. Isso corrige o
defeito de V002 (unique por decisão inviabilizava bulk >1 campo).
Rollback manual documentado: `DROP TABLE` em ordem reversa — não
implementado como migration (apenas `up`, sem reset destrutivo).

## LGPD / Retenção (GATE-B)

Classificação completa: `supplier-enrichment-retention-classification.md`.
Resumo: metadados de revisão (§6/§7 ROPA), decisões/eventos como audit log
(§2, 2 anos), valores de proposta = dados cadastrais corporativos públicos,
`expires_at` = `ENRICHMENT_REVIEW_TTL_HOURS` (default 24h — pendente B-02 PO).
Endosso formal do DPO pendente (residual declarado).

## Prepare-update

`POST …/prepare-update` revalida baseline (fingerprint SHA-256 do snapshot
canônico relido via api-delpi). Divergência → review → `STALE` + `409`.
Resposta: `{review_id, revision, supplier, baseline_status: "CURRENT",
write_gate_enabled: false, draft_fields: [{field_key, current_value,
proposed_value, proposal_id, decision_id}]}` — somente campos aceitos +
elegíveis + COMPARABLE; `tax_id`, identidade e informativos nunca entram.
