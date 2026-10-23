# X4.UX-R1.P0 — Inventário & Contract Freeze (2026-10-23)

> **SCOPE:** inventário técnico, congelamento de contratos candidatos e plano por
> fatias. **Nenhuma implementação** nesta execução. Base: decisões PO
> `X4-UX-R1-CADASTRO-ASSISTIDO-CONFERENCIA-DECISOES-20261023.md` + plano
> `X4-UX-R1-IMPLEMENTATION-PLAN-FRONTEND-BACKEND-20261023.md` (revalidados no HEAD).
> BASE HEAD `3793283437` → ORIGIN `dec7812bc9` (pull ff-only).

## 1. Matriz de rotas — reconciliada com código real

| Ação do usuário | MFE | BFF | Owner de dados | AuthZ | Estado |
|---|---|---|---|---|---|
| Cadastro manual | `SupplierCreatePage` (`/suppliers/new`) | `POST /suppliers` (gated) | api-delpi | `can_use_operations` + Core | **PROVEN** |
| Lista E13 | `SuppliersPage` | `GET /suppliers` → api-delpi `/supplies/suppliers` | api-delpi SA2 | idem | **PROVEN** |
| Ficha E14 | `SupplierDetailPage` | `GET /suppliers/{code}/{store}` | api-delpi | idem | **PROVEN** |
| Enriquecimento E14 | `enrichment/` `#enrichment` | 7 rotas S2 `enrichment-reviews` | supplies-api PG | idem + actor ownership | **PROVEN** |
| Buscar CNPJ (preview) | a implementar | `POST /suppliers/creation-preview` | external-data-api | Core/BFF/S2S | **TARGET** |
| Buscar razão social | a implementar | `GET /suppliers/external-search` | provider externo via external-data-api | Core/BFF/S2S | **TARGET** — bloqueado por provider |
| Selecionar empresa | a implementar | mesmo `creation-preview` | external-data-api | idem | **TARGET** |
| Ver divergências E13 | a implementar | `POST /suppliers/enrichment-summaries` (ver §4.3) | supplies-api PG | Core/BFF | **TARGET** |
| Revisar divergência | `EnrichmentSection` | S2 existente | supplies-api | idem | **PROVEN** |

**Colisões de rota (verificado):** `creation-preview`, `external-search`,
`enrichment-summaries` são segmento único sob `/suppliers/` — não colidem com
`/<code>/<store>` (dois segmentos) nem com `/catalogs/<catalog>`,
`/postal-codes/<cep>`, `/operations/<id>` (prefixos literais distintos).
`POST /suppliers/creation-preview` não conflita com `POST /suppliers` (path exato).

## 2. Inventário frontend

`SupplierCreatePage` (388 ln): `SupplierCreateDraft` = dict de strings indexado
pelas chaves do `SUPPLIER_FIELD_REGISTRY` (23 campos), `patchDraft` é o ponto
único de mutação, `dirty`, `reviewing`→modal, `confirmSubmit`→`createSupplier`
com `classifyWriteOutcome` (ACK≠persistência). Sem estado externo — **extensão
natural:** seletor de modo antes do formulário + `provenance: Record<field_key,
{source,retrieved_at,status}>` paralelo ao draft. Nenhum novo formulário.

`SuppliersPage`: toolbar/filtros/paginação server-side + `history.replaceState`
(F5-safe). Coluna «Conferência» entra como cell derivada de dados do summary
batch — sem alterar a query da lista Protheus.

`enrichment/`: tipos DTO 1:1, `decisionOperations` (retry imutável), content PT-BR
+ error map — **padrão a replicar** para `creation/` (novo submódulo).

Estrutura proposta (menor diff):
```
features/suppliers/creation/
  api.ts            creation-preview + external-search
  types.ts          DTOs do freeze (§4)
  stateMachine.ts   pure gates: modo, overwrite de campos editados, proveniência
  content.ts        copy PT-BR + errors
  CreationAssistedFlow.tsx   seletor CNPJ | razão social | manual
  CreationSuggestionsPanel.tsx  sugestões + proveniência por campo
```
`SupplierCreatePage` recebe `mode` state; `patchDraft` nunca sobrescreve campo já
editado sem confirmação (regra em `stateMachine`, testável).

## 3. Inventário backend

**supplies-api:** `POST /suppliers` = forwarder gated → api-delpi
`/integrations/protheus/suppliers` (`sanitize_post_body` → `POST_SUPPLIER_FIELDS`
23 keys, `IDENTITY_FORBIDDEN_FIELDS` rejeitados). **Port já pronto:**
`ExternalDataApiCompanyRegistryProvider` implementa `CompanyRegistryProvider`
→ `GET {EXTERNAL_DATA_API_BASE_URL}/v1/cnpj/{cnpj}` S2S — o mesmo port serve o
preview (sugestões externas) sem nova integração. `registry_rate_limits` +
`review_service` já provêm per-actor limiting e proveniência.

**external-data-api:** `GET /v1/cnpj/<cnpj>` apenas — `LookupCnpjUseCase` +
provider port + `require_s2s_service` allowlist + rate limit + correlation id.
`/v1/companies/search` encaixa como nova rota + novo provider port — **provider
externo é o único bloqueio real**.

**api-delpi:** `GET /supplies/suppliers?query=` faz `A2_CGC LIKE` (contém) —
busca textual, **não é duplicate-check**. `POST /integrations/protheus/suppliers`
aceita `fornecedor` map (gate write OFF). `GET /integrations/protheus/suppliers/{id}`
é o read canônico.

## 4. Contratos candidatos (FREEZE proposto)

### 4.1 `POST /suppliers/creation-preview` — owner supplies-api

- **Body:** `{"tax_id": "<14 dígitos>"}` (POST, não GET — CNPJ no corpo, não em URL/log).
- **AuthZ:** `require_policy(can_use_operations)` + Core effective + fail-closed.
- **Resposta:** `{"tax_id_masked","person_type","duplicate_check":{"status":"CLEAR|POSSIBLE_MATCH|INCONCLUSIVE","matches":[{supplier_code,supplier_store,supplier_name,state}]},"suggestions":[{field_key,suggested_value,source:{provider_id,retrieved_at},applicable:bool}],"unavailable_fields":[...],"write_enabled":false}`.
- **Erros:** 400/422 formato, 401, 403, 404 CNPJ não localizado, 409 duplicidade confirmada (quando check canônico), 429+Retry-After, 502 schema inválido, 503/504 provider.
- **Semântica:** zero persistência; `INCONCLUSIVE` nunca vira `CLEAR`; suggestions
  limitadas a `POST_SUPPLIER_FIELDS` ∩ mapping S1; campos internos (payment_condition,
  accounting_account, financial_nature, código/loja, codusr) nunca sugeridos.

### 4.2 `GET /suppliers/external-search` — owner supplies-api → external-data-api

- **Query:** `q` (min 3, max 200), `state?` (UF), `city?`, `page`, `page_size` ≤50.
- **Resposta:** `{items:[{legal_name,trade_name,tax_id_masked,city,state,establishment_kind:"MATRIX|BRANCH",source:{provider_id,retrieved_at}}],page,page_size,total}`.
- **Anti-abuso:** rate limit por ator + global + mínimo de query; sem retorno de CPF/QSA.
- **Dependência:** `/v1/companies/search` em external-data-api — **BLOCKED até provider homologado** (§5).

### 4.3 `POST /suppliers/enrichment-summaries` — owner supplies-api (decisão de freeze)

Escolhido batch-POST sobre extensão de `GET /suppliers`: a lista vem da api-delpi
(paginação canônica) e o resumo é read-model próprio em PG — composição em
endpoint separado preserva contratos, evita N+1 (uma query IN por até 100 pares)
e não expõe revisões de outros atores.

- **Body:** `{"suppliers":[{"code","store"}, …≤100]}`.
- **Resposta:** `{items:[{supplier_code,supplier_store,status:"NOT_CHECKED|NEEDS_REVIEW|IN_REVIEW|REVIEWED|STALE","actionable_pending":int,"last_checked_at","source_id","review_id"}]}` — somente a revisão mais recente **do ator chamador** (ownership S2 vigente); ausência de linha = `NOT_CHECKED` implícito.
- **Regra `actionable_pending` (freeze):** `decision_state=PENDING AND comparison_state IN (DIFFERENT, CURRENT_MISSING) AND eligibility_state=ELIGIBLE_TO_APPLY`. `MATCH`, `SOURCE_MISSING` (dado interno preservado — D-02), `PROTECTED`, `NOT_COMPARABLE`, `UNSUPPORTED`, `ERROR`, `PENDING_VALIDATION` e `NOT_APPLICABLE` **não contam**. Derivação pura sobre propostas persistidas — **zero mudança de domínio S2**, zero enum novo.
- **Sem chamadas externas** no caminho do summary (read-model PG apenas).

### 4.4 Duplicate check — **LACUNA DE CONTRATO em api-delpi**

`GET /supplies/suppliers?query=` usa `LIKE` — textual, não prova inexistência.
**Menor contrato proposto (owner api-delpi):** `GET /supplies/suppliers?tax_id=<14 dígitos>`
com match **exato** normalizado em `A2_CGC` + filtro de empresa/filial pelo
escopo vigente. Até existir, `duplicate_check.status` no preview = `POSSIBLE_MATCH`
(quando LIKE retorna candidatos) ou `INCONCLUSIVE` — **nunca `CLEAR`**.

## 5. Provider assessment — busca nominal (RQ-03)

BrasilAPI: **sem busca por nome** (lookup exato CNPJ apenas) — não serve.

Candidatos identificados (todos comerciais, base pública RFB):

| Provider | Busca por nome | Filtros UF/município | Matriz/filial | Observações |
|---|---|---|---|---|
| CNPGolden | `GET /search/by-name` (≥3 chars) | sim | sim (estabelecimentos) | plano pago; OpenAPI; dados RFB mensais |
| ZenPJ | `GET /companies?q=` (razão+fantasia, `nameField`) | `state`, cidade, CNAE | sim | free tier 100/mês; RFC 9457 errors |
| Nume | `GET /v1/empresas?nome=` (prefixo) | `uf,municipio` | via `?completo=1` | créditos por chamada |
| CNPJota | `GET /api/v1/empresas/busca` | `uf` | — | paginado, limite 100 |
| RFB dados abertos | dataset bulk | — | — | exigiria serviço/indexação própria — fora de escopo |

**Classificação: `TO_INVENTORY`** — nenhum homologado; licenciamento, LGPD/ROPA,
SLA, custos e contrato de dados precisam de decisão PO/DPO **antes** de R1.S3.
Fallback arquitetural preservado: R1.S1+S2 (CNPJ direto) e R1.S5+S6 (conferência)
**não dependem** do provider nominal.

## 6. Segurança — verificado

- Fail-closed existente: `require_policy(can_use_operations)` + Core effective +
  unit scope + actor ownership (S2). Nenhuma permission nova proposta.
- S2S individual já vigente (`supplies-api`→`external-data-api` allowlist).
- CNPJ em body (POST) evita vazamento em URL/logs; `tax_id_masked` no retorno
  salvo autorização específica.
- Write gate ERP OFF preservado; preview não chama `POST /suppliers`.

## 7. Plano por fatias (revisto — dependências reais)

| Etapa | Owner | Pré-condição | Entrega | Stop |
|---|---|---|---|---|
| **R1.S1** preview CNPJ | supplies-api (+api-delpi p/ dup-check exato) | Este P0 + GO | Endpoint + mapper allowlist + errors + testes | duplicate-check sem contrato canônico → entregar `INCONCLUSIVE` honesto ou bloquear |
| **R1.S2** MFE manual+CNPJ | plugins/supplies | S1 aceito | Seletor 3 modos (nominal disabled), proveniência, draft preservado | provider não pronto ≠ bloqueio |
| **R1.S3** busca nominal | external-data-api | **provider homologado + LGPD/DPO** | `/v1/companies/search` | sem provider → registrar blocker |
| **R1.S4** BFF+MFE nominal | supplies-api + MFE | S3 PASS | external-search + seleção → preview automático | — |
| **R1.S5** summary E13 | supplies-api | regra §4.3 | batch summaries read-model | semântica contestada → freeze de novo |
| **R1.S6** MFE conferência | plugins/supplies | S5 PASS | coluna status/counter/atalho | summary falha → parcial, lista intacta |
| **R1.S7** runtime | Deploy + PO | fatias materiais | bundle SHA + smoke + rollback | smoke ausente = INCONCLUSIVE |

**Paralelismo legítimo:** {S1→S2} ∥ {S5→S6}; {S3→S4} independente (bloqueado externamente).

## 8. RQ/AC — cobertura do freeze

RQ-01..RQ-06 mapeados a contratos acima. Testes planejados por fatia (§7 do plano
aprovado mantém-se válido): positive/sibling/negative por endpoint, sem N+1,
403/401/429/503, duplicidade INCONCLUSIVE≠CLEAR, zero POST ERP.
**TESTS EXECUTED: TEST_NOT_RUN** (P0 documental).

## 9. Execução

- **FILES INSPECTED:** `suppliers_routes.py`, `suppliers_dto.py`,
  `supplier_enrichment_routes.py`, `external_data_company_registry_provider.py`,
  `comparison.py`, `review_lifecycle.py`, `field_mapping.py`,
  `suppliers_router.py` (api-delpi), `totvs_supplier_repository.py`,
  `cnpj_routes.py`, `s2s_auth.py` (external-data-api), `SupplierCreatePage`,
  `SupplierFormFields`, `types.ts`, `enrichment/*`, ambos docs X4-UX-R1.
- **FILES CHANGED:** este documento.
- **EXECUTION_DRIFT:** nenhum — inventário confirma as premissas do plano aprovado;
  duas especificações do plano refinadas (§4.3 endpoint batch; §4.4 lacuna dup-check).

**STATUS: `READY_TO_AUTHORIZE` para R1.S1** — com a ressalva registrada: o
duplicate-check exato depende do menor contrato api-delpi (§4.4); S1 pode entregar
`POSSIBLE_MATCH/INCONCLUSIVE` sem ele, e a criação permanece gated de qualquer forma.
R1.S3 está **BLOCKED** (provider/LGPD) até homologação externa.
