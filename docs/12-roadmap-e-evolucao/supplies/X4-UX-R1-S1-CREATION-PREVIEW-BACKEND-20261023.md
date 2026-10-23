# X4.UX-R1.S1 — Supplier Creation Preview backend (2026-10-23)

> **SCOPE:** backend somente. BASE HEAD `90497ef43d` → ORIGIN `ae33b30dce`.
> Contrato congelado em `X4-UX-R1-P0-INVENTORY-CONTRACT-FREEZE-20261023.md` §4.1/§4.4.
> **Zero escrita** — nenhum POST/PUT ERP, nenhuma persistência, nenhuma migration.

## 1. Endpoint implementado

```
POST /suppliers/creation-preview        (BFF público /apps/supplies-api)
Authorization: Bearer <user JWT>
{ "tax_id": "<14 dígitos, com ou sem máscara>" }
```

- **Route:** `supplier_creation_routes.py` (blueprint `supplier_creation`,
  registrado em `root_composer.py`).
- **AuthZ:** `require_policy(can_use_operations)` → `supplies.access` efetiva
  via Core; fail-closed. Nenhuma permission nova.
- **Request:** allowlist estrita `{tax_id}` — qualquer campo extra
  (incl. `actor`, `unit_context`, `source_id`) → `422 invalid_request`.
- **Validação:** dígitos normalizados + **dígitos verificadores** CNPJ —
  rejeição local antes de qualquer integração.
- **Rate limit:** `registry_rate_limiter().acquire("actor", user.id)` — o mesmo
  budget per-actor da consulta externa (429 + `Retry-After`).

## 2. Orquestração (read-only)

```text
route → SupplierCreationPreviewService
  ├── CompanyRegistryProvider.fetch(tax_id)     → external-data-api → BrasilAPI
  │     (port S2 existente reutilizado, zero nova integração)
  └── SupplierDuplicateSearchPort             → api-delpi
        GET /supplies/suppliers?tax_id=<digits>  (match EXATO, novo)
```

`DelpiSupplierDuplicateSearch` usa o `DelpiS2SApiGateway` compartilhado
(S2S individual + JWT do usuário). Falha do duplicate-check **não** derruba o
preview: `status=INCONCLUSIVE` — nunca `CLEAR` por falha.

## 3. Response DTO

```jsonc
{
  "tax_id_masked": "00.***.***/0001-**",      // root+branch visíveis, DV oculto
  "person_type": "J",                          // derivado do tipo de documento
  "duplicate_check": {
    "status": "CLEAR | POSSIBLE_MATCH | INCONCLUSIVE",
    "matches": [ { supplier_code, supplier_store, supplier_name,
                   state, blocked } ]           // ≤10, identificação mínima
  },
  "suggestions": [
    { "field_key": "supplier_name", "suggested_value": "...",
      "source": { "provider_id": "brasilapi-cnpj-v1",
                  "retrieved_at": "<provider timestamp>" },
      "applicable": true }
  ],
  "unavailable_fields": [ "payment_condition_code", ... ],
  "write_enabled": false                       // preview nunca persiste
}
```

- `CLEAR` só é emitido quando a busca **exata** canônica retornou `total=0`
  com sucesso. `total>0` → `POSSIBLE_MATCH`. Falha upstream → `INCONCLUSIVE`.
- `write_enabled=false` significa "esta operação não grava" — o gate de
  criação segue upstream-controlled em `POST /suppliers` (inalterado).

## 4. Regras de campo (domínio puro)

`app/domain/supplier_creation/preview.py` + `CNPJ_SA2_MAPPING_V1`:

- Só `FieldClass.COMPARABLE` com `source_field` e valor presente.
- `requires_trusted_source_policy` (contact.*) → **nunca sugerido**
  (minimização LGPD já retém upstream; defesa em profundidade aqui).
- `requires_equivalence_rule` (`supplier_short_name` ← trade_name) →
  retornado com `applicable=false` (revisão manual, nunca auto-aplicado).
- `PROTECTED`/`INFORMATION_ONLY` → fora das sugestões.
- Normalização de *display* (sem case-fold; acentos preservados) + truncamento
  ao `max_length` SA2.
- `unavailable_fields` = `POST_SUPPLIER_FIELDS` − sugeridos −
  `{tax_id, person_type}` → campos para preenchimento manual.
- Nunca sugeridos: código, loja, condição de pagamento, conta contábil,
  natureza financeira, QSA/CPF, contatos externos — por ausência de mapping.

## 5. Duplicate check — lacuna do P0 fechada

api-delpi ganhou filtro **exato** e read-only:

```
GET /supplies/suppliers?tax_id=<digits>
→ REPLACE(REPLACE(REPLACE(SA2.A2_CGC,'.',''),'/',''),'-','') = ?
```

- Normalização de dígitos no DTO (`11|14` chars; `ValueError` → 400).
- ANDed com `A2_FILIAL=''` / `D_E_L_E_T_=''` / `state` / `blocked` — nunca
  ORed no `query` textual; semântica de `query` inalterada.
- Mesmo envelope paginado + `filters.tax_id` ecoado.
- AuthZ inalterada (`require_s2s_or_any_permission` + `suppliers.read` +
  allowlist `supplies-api`).

## 6. Erros

| Situação | HTTP | code |
|---|---|---|
| sem Bearer / sem capability | 401 / 403 | (middleware/policy) |
| body não-objeto, campos extras, CNPJ inválido | 422 | `invalid_request` |
| CNPJ inexistente no provedor | 404 | `ENRICHMENT_REGISTRY_TAX_ID_NOT_FOUND` |
| rate limit | 429 | `ENRICHMENT_RATE_LIMITED` + Retry-After |
| limiter indisponível | 503 | `ENRICHMENT_RATE_LIMITER_UNAVAILABLE` |
| payload externo inválido | 502 | `ENRICHMENT_REGISTRY_INVALID_RESPONSE` |
| provider/S2S indisponível | 503 | `ENRICHMENT_SOURCE_UNAVAILABLE` |
| api-delpi falha | — | `duplicate_check.status=INCONCLUSIVE` (preview não falha) |

## 7. Testes

- `tests/domain/test_supplier_creation_preview.py` — CNPJ DVs, máscara,
  classificação de duplicidade, mapper (sugeridos × protegidos × contato ×
  info-only × truncamento × ausência).
- `tests/application/test_supplier_creation_preview_service.py` — shape,
  proveniência, unavailable, POSSIBLE_MATCH mínimo, INCONCLUSIVE por falha,
  erros propagando.
- `tests/test_supplier_creation_routes.py` — 401/403/422/404/429+Retry-After,
  normalização de máscara, sucesso, **zero `post`/`put` no gateway**.
- `api-delpi/tests/test_supplies_suppliers_list.py` — SQL exato (REPLACE=),
  AND vs OR, DTO `tax_id`, regressão sem o filtro.

**Resultado:** supplies-api `425 passed, 21 skipped` (skips PG-dependentes
pré-existentes); api-delpi alvo `23 passed`; sweep supplies/supplier api-delpi
`536 passed` + **3 falhas pré-existentes** confirmadas no baseline (checkout
principal, sem este diff): DAVI product-master intents e CPV meta — sem relação
com o diff.

## 8. AC coverage

AC-01..16 `PASS` por teste/código; AC-17 esta doc + plano; AC-18 commit/push.
`TEST_NOT_RUN`: smoke em runtime (deploy não autorizado nesta fatia).

## 9. Residuais / próxima etapa

- Runtime smoke fica para R1.S7.
- `POSSIBLE_MATCH` usa match exato de CNPJ; identidade jurídica definitiva
  (mesma empresa, CNPJ diferente) permanece decisão do usuário — conforme RQ-04.
- Próximo gate: **X4.UX-R1.S2** (MFE — seletor de modo + proveniência sobre o
  formulário existente). R1.S3 segue `BLOCKED` (provider nominal).
