# X4.P0 — Supplier Enrichment UX: inventário real, contrato UX e freeze

> **Estado:** P0 fechado (2026-10-22). Inventário em HEAD `72427d5017`. Documento de decisão e contrato UX — **não** autoriza implementação visual (X4.S1), deploy, escrita Protheus nem promoção de página.
> **Escopo X4:** enriquecimento cadastral assistido (SA2 × BrasilAPI → revisão S2 → decisões → prepare-update draft-only). BrasilAPI é fonte de **sugestão**, nunca autoridade. `write_gate_enabled=false` permanece.

## 1. Baseline e authorities lidos

- HEAD `72427d5017`, `origin/main` `ebe86d3180` (avançou — rebase antes de push).
- `instrucoes-oficiais-gpt-arquiteto-delpi-central.md`, `.cursor/rules` (evidence-driven, centralized-rules, frontend/MFE, api-contracts, plan-execution).
- Contratos: `supplier_enrichment_routes.py` (rotas reais), `models.py`/`comparison.py`/`review_lifecycle.py` (S1/S2), `protheus_router.py` (owner api-delpi).
- `FORNECEDORES-GESTAO-CADASTRAL-ROADMAP.md`, `FORNECEDORES-RETOMADA-IMPLEMENTACAO-2026-10-20.md`, `IMPLEMENTATION-PLAN.md`, `SUPPLIES-ENRICHMENT-01-BRASILAPI-MVP-DECISION-20261022.md`, `X3-RUNTIME-EVIDENCE-20261022.md` (E2E + rework).
- Documento de transição citado na task (`X3-E2E-CLOSURE-AND-X4-UI-READINESS-20261022.md`) **não existe** no HEAD — este P0 cumpre esse papel. `TO_INVENTORY` se o PO possuir versão externa.

## 2. Gate de sequenciamento — estado real

| Item | Estado em HEAD | Evidência |
|---|---|---|
| E10 / WF-15 (Estoque) | `IN_PROGRESS`; S1–S3 PASS, **S4 INCONCLUSIVE** — bundle federado sem `InventoryPage`, `DEPLOY_REQUIRED=YES` | `IMPLEMENTATION-PLAN.md` + `e10-wf15-s4-final-acceptance.md` |
| E13 / WF-09 (lista) | **Implementada** — `SuppliersPage` com busca `query`, filtro `state`/`blocked`, paginação server-side, URL/F5 (`parseQueryFromSearch`/`buildUrlSearch`), forbidden/404/empty/error | `features/suppliers/SuppliersPage.tsx`, `query.ts`, `api.ts` |
| E14 / WF-10 (ficha) | **Implementada** — `SupplierDetailPage` com 5 seções, registry de 23 campos (`SUPPLIER_FIELD_REGISTRY`), edição com diff (`diffEditableFields`+`SupplierReviewTable`), `SupplierPostalCodeAssistant` (precedente lookup externo→sugestão), outcome ACK≠persistência | `SupplierDetailPage.tsx`, `SupplierFormFields.tsx`, `types.ts` |
| Rotas MFE | `/suppliers`, `/suppliers/new`, `/suppliers/{code}/{store}` registradas em `pluginRoutes.ts` e no catálogo hub ("Operações→Fornecedores") | `pluginRoutes.ts`, `pluginRouteCatalog.ts`, `supplies.manifest.json` |

**Reconciliação pendente (não silenciar):** `IMPLEMENTATION-PLAN.md` ainda lista E13/E14 como placeholders nominais e E10.S4 inconclusivo. A retomada de fornecedores (`FORNECEDORES-RETOMADA-2026-10-20`) autorizou a frente prioritária e as páginas foram entregues/deployadas, mas a **promoção formal na fila ainda não foi reconciliada** (pendência #1 do próprio documento).

**Proposta de sequenciamento (X4 não altera a fila):**
- X4 **não é página nova**: estende a ficha E14 já existente (`/suppliers/{code}/{store}`) com uma seção de enriquecimento + ação de entrada na lista E13. Sem nova rota, sem mudança de manifest.
- X4.S1 fica sob a mesma linhagem de autorização da retomada de fornecedores + decisão BrasilAPI MVP (item 3: "o fluxo MVP… revisão S2 → decisões usuário → prepare-update draft only").
- A recomendação formal ao PO: registrar na próxima reconciliação do `IMPLEMENTATION-PLAN.md` que E13/E14 estão implementadas em runtime e que X4.S1 é **incremento de E14**, não promoção de página nova. E10.S4 segue inconclusivo e independente (página `/inventory`, sem dependência de X4).

**Sem EXECUTION_DRIFT:** a task autoriza X4.P0 e o inventário confirma dependência visual já entregue; não há conflito que impeça documentação/planejamento.

## 3. Onde a experiência X4 reside

```text
E13 /suppliers                    (lista — ponto de entrada opcional)
  └─ ação na linha: "Enriquecer cadastro" → deep link E14#enrichment
E14 /suppliers/{code}/{store}     (ficha — casa canônica da jornada X4)
  └─ nova seção "Enriquecimento cadastral" (âncora #enrichment):
       1. Estado inicial + CTA "Consultar dados externos"
       2. Revisão ativa: comparação campo a campo + decisões
       3. Resumo de decisões + prepare-update (draft)
       4. Histórico de revisões do ator (paginado)
```

Racional: a decisão S1/S2 é sempre sobre **um** fornecedor; a ficha E14 já carrega o snapshot canônico, as seções cadastrais e os padrões de help/feedback. Lista serve apenas de entrada.

## 4. Inventário plugin-ui — REUSE_DECISION

Kit bound em `suppliesUi.ts` (prefixo `sp`, scope `.dashboard-supplies-portal`). Para X4:

| Necessidade UX | Equivalente | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|---|
| Cabeçalho/breadcrumb | `SuppliesPagePath`, `SuppliesPageHero` | YES | REUSE |
| CTA consulta/ações | `SuppliesActionButton` | YES | REUSE |
| Seção + help | `SuppliesSectionCard`, `SuppliesSectionHintLabel`, `HelpTooltip` | YES | REUSE |
| Loading | `SuppliesLoadingCard` | YES | REUSE |
| Empty/erro/forbidden | `SuppliesEmptyState`, `SuppliesStateBanner` | YES | REUSE |
| Status de comparação/decisão (badge) | `SuppliesStatusBadge` (variants neutral/info/success/warning/danger) | YES | REUSE |
| Tabela campo-a-campo | `SuppliesDataTable` + `DataTableColumn` | YES | REUSE |
| Decisão por linha | `SuppliesActionButton` ghost/primary por linha (`rowClick:"stop"`/`interactive`) | YES | REUSE |
| Bulk decisions | Seleção múltipla por checkboxes em coluna `interactive` + barra `SuppliesDataListToolbar` | YES | REUSE (composição) |
| Modal de confirmação | `SuppliesModal` | YES | REUSE (bulk ACCEPT + prepare-update) |
| Histórico de revisões | `SuppliesDataTable` + `SuppliesCompactPagination` | YES | REUSE |
| Fonte/timestamp | texto + `SuppliesStatusBadge` (`source_id`, `source_retrieved_at`) | YES | REUSE |
| Identidade fornecedor | `SuppliesEntityAvatarLabel` / `SuppliesDirectoryIdentity` | YES | REUSE |
| Diff campo atual × sugerido | precedente `SupplierReviewTable`/`diffEditableFields` (local supplies) | YES (local) | REUSE/EXTEND local — comparação tem 2 colunas fixas + badge; adaptar padrão, não criar genérico no kit |
| Proveniência externa | nenhum badge dedicado | NO | manter local: rótulo "Fonte: BrasilAPI · consultado em …" — sem `ProvenanceBadge` genérico (1 consumidor) |

**Decisão:** zero componentes novos no `@delpi/plugin-ui`. Toda composição específica de enriquecimento fica em `plugins/supplies/src/features/suppliers/` (não pertence ao kit genérico — regra do roadmap §4).

## 5. Jornada UX e wireframe textual

```text
┌─ E14 — Ficha do fornecedor 002469/01 ─────────────────────────────┐
│ … seções cadastrais existentes …                                  │
│                                                                   │
│ ── Enriquecimento cadastral  [?help] ─────────────────────────    │
│   Fonte: BrasilAPI (brasilapi-cnpj-v1) — dados públicos de        │
│   pessoa jurídica, apenas sugestão. Não grava no Protheus.        │
│                                                                   │
│   [Estado 0] Nenhuma revisão ativa                                │
│   [ Consultar dados externos (BrasilAPI) ]  → POST reviews        │
│                                                                   │
│   [Estado 1] Revisão IN_REVIEW rev=N · consultada 22/10 14:32     │
│   ┌ Resumo: 3 divergências · 6 iguais · 7 não comparáveis ─────┐ │
│   │ Campo          │ Atual (Protheus) │ Sugerido (BrasilAPI)  │ │
│   │ Razão social   │ RODRIGUES KANN.  │ RODRIGUES KANNENBERG  │ │
│   │                │                  │ ⚠ DIFFERENT [Elegível]│ │
│   │ CEP            │ 12345-000        │ 12345-678            │ │
│   │                │                  │ ⚠ DIFFERENT [Elegível]│ │
│   │ Cidade         │ São Paulo        │ São Paulo            │ │
│   │                │                  │ ✓ MATCH               │ │
│   │ Telefone       │ —                │ fonte não fornece    │ │
│   │                │                  │ ○ SOURCE_MISSING      │ │
│   │ CNPJ           │ 12.345.678/0001  │ 🔒 PROTECTED          │ │
│   │ [☑] selecionar p/ bulk                                       │ │
│   └─────────────────────────────────────────────────────────────┘ │
│   Por linha: [Aceitar] [Rejeitar]  ·  Toolbar:                    │
│   [Aceitar selecionados] [Rejeitar selecionados] (modal confirma) │
│                                                                   │
│   [Estado 2] Decisões registradas · rev=N+1                       │
│   Aceitos: 2 · Rejeitados: 14 · Pendentes: 0                      │
│   [ Preparar atualização (rascunho) ] → POST prepare-update       │
│                                                                   │
│   [Estado 3] Draft — NÃO gravado no Protheus                      │
│   "Rascunho para conferência. Nenhum dado foi alterado no ERP."   │
│   Campo: Razão social → "RODRIGUES KANNENBERG"  · write_gate=OFF  │
│                                                                   │
│   Histórico de revisões (do usuário) — tabela paginada            │
│   ID · fonte · consulta · status · rev · ações (abrir)            │
└───────────────────────────────────────────────────────────────────┘
```

Regras de decisão UI (espelham o backend, nunca duplicam autoridade):
- `decision_state=PENDING` + `eligibility=ELIGIBLE_TO_APPLY` → Aceitar e Rejeitar habilitados.
- `PENDING` + não elegível → somente Rejeitar; tooltip com `eligibility_reason`.
- Já decidido → somente leitura (servidor devolveria 409 `ENRICHMENT_PROPOSAL_ALREADY_DECIDED`).
- Review `DECIDED`/expirada → sem ações; CTA para nova consulta.
- `person_type != "J"` → criação falha com 422 `ENRICHMENT_UNSUPPORTED_DOCUMENT` → banner explicativo (fornecedor PF/outros não suportado).
- Nunca exibir contatos/QSA/CPF (backend já exclui; UI não renderiza campos fora da matriz de 16).

## 6. Matriz endpoints × ação × authz × estado × erro

| BFF endpoint | Ação UI | AuthZ | Estado UI | Erros reais (code) |
|---|---|---|---|---|
| `POST /suppliers/{c}/{s}/enrichment-reviews` | "Consultar dados externos" | `supplies.access` + ownership | `creating`(loading) → `review_active` | 422 `ENRICHMENT_UNSUPPORTED_DOCUMENT` · 404 `ENRICHMENT_REGISTRY_TAX_ID_NOT_FOUND`/`not_found` · 422 `ENRICHMENT_REGISTRY_INVALID_TAX_ID` · 502 `ENRICHMENT_REGISTRY_INVALID_RESPONSE` · 503 `ENRICHMENT_SOURCE_UNAVAILABLE`/`ENRICHMENT_RATE_LIMITER_UNAVAILABLE` · 429 `ENRICHMENT_RATE_LIMITED`(+Retry-After) · 401/403 |
| `GET …/enrichment-reviews` | histórico (paginado ≤50) | idem | `history_loading/empty/ready/error` | 401/403/404 |
| `GET …/enrichment-reviews/{id}` | abrir revisão/F5 | idem | `review_loading/error` | 404 `not_found` · 403 `forbidden` |
| `POST …/decisions` | aceitar/rejeitar campo | idem | `deciding` → refresh `review+proposals`; `idempotent_replay=true` → toast "já registrada" | 409 `ENRICHMENT_REVISION_CONFLICT`/`ENRICHMENT_IDEMPOTENCY_CONFLICT`/`ENRICHMENT_PROPOSAL_ALREADY_DECIDED`/`ENRICHMENT_STALE_BASELINE`/`ENRICHMENT_REVIEW_CANCELLED` · 410 `ENRICHMENT_REVIEW_EXPIRED` · 422 `ENRICHMENT_PROPOSAL_NOT_ELIGIBLE`/`invalid_request` |
| `POST …/bulk-decisions` | aceitar/rejeitar seleção (modal confirma) | idem | idem, atômico | idem |
| `GET …/decisions` | trilha de decisões (auditoria visual) | idem | lista read-only | 401/403/404 |
| `POST …/prepare-update` | "Preparar atualização" | idem | `draft` (read-only) — sempre `write_gate_enabled=false` | 409 revision/stale · 410 expired · 401/403/404 |

Body das decisões: `{field_key|field_keys, decision:"ACCEPT"|"REJECT", expected_revision, idempotency_key, reason_code?}`. `idempotency_key` gerada client-side por ação (UUID); **replay do mesmo request reusa a mesma chave + mesmo payload** (retry de rede seguro); nova tentativa com payload diferente = nova chave — nunca reuse com payload divergente (409 por contrato). `expected_revision` sempre o `review.revision` corrente.

## 7. Matriz de estados e mensagens PT-BR

| Estado/erro | Comportamento UI | Mensagem PT-BR (proposta) |
|---|---|---|
| loading | `SuppliesLoadingCard` | "Consultando dados externos…" |
| empty (sem revisões) | `SuppliesEmptyState` + CTA | "Nenhuma consulta de enriquecimento ainda. Consulte a fonte externa para comparar o cadastro." |
| review IN_REVIEW | tabela de comparação | — |
| revisão expirada (410) | banner + CTA nova consulta | "Esta revisão expirou. Inicie uma nova consulta para comparar dados atualizados." |
| baseline stale (409) | banner + recarregar | "O cadastro do fornecedor mudou desde a consulta. Recarregue e revise novamente." |
| revision conflict (409) | banner + refresh automático de revisão | "A revisão foi atualizada em outra ação. Os dados foram recarregados." |
| idempotency conflict (409) | banner | "Operação já registrada com dados diferentes. Nenhuma duplicação foi aplicada." |
| fonte indisponível (503) | banner + retry manual | "A fonte externa está temporariamente indisponível. Tente novamente em instantes." |
| rate limit (429) | banner + Retry-After | "Limite de consultas atingido. Aguarde alguns segundos e tente novamente." |
| CNPJ não encontrado (404) | banner informativo | "CNPJ não localizado na fonte externa." |
| documento não suportado (422) | banner | "O enriquecimento externo é disponível apenas para pessoa jurídica (CNPJ)." |
| sem divergências | empty parcial | "Nenhuma divergência encontrada — o cadastro está alinhado à fonte externa." |
| sem elegíveis | aviso | "As divergências encontradas não são elegíveis para aplicação." |
| tudo decidido → DECIDED | resumo + CTA draft | — |
| draft vazio | banner | "Nenhum campo aceito — não há rascunho de atualização." |
| draft pronto | banner success | "Rascunho preparado. Nenhum dado foi gravado no Protheus." |
| forbidden (403) | `SuppliesEmptyState` | "Você não tem acesso a esta revisão." |
| partial | histórico falha ≠ bloquear review | "Histórico indisponível no momento; a revisão atual continua utilizável." |

## 8. Segurança (matriz AuthZ)

- `supplies.access` via Core — única permissão; **nenhuma permission nova** por botão/tela.
- Ownership por ator no backend (`actor_subject` server-side); UI nunca envia ator/fonte/snapshot — campos server-owned rejeitados pelo BFF.
- MFE chama somente `supplies-api`; zero chamada direta a api-delpi/BrasilAPI; nenhum token S2S no frontend.
- Sem contatos, QSA, CPF ou dados pessoais da fonte externa na UI.
- Sem ação de "Salvar no Protheus" enquanto `write_gate_enabled=false` — o draft é sempre apresentado como não gravado.

## 9. RQ/AC

| RQ | Requisito | AC | Teste |
|---|---|---|---|
| RQ-X4-01 | Pesquisar e abrir fornecedor | fluxo E13 existente inalterado | `suppliers.test.ts` + smoke |
| RQ-X4-02 | CTA consulta externa explícita | POST review → 16 propostas renderizadas | unit + integração MSW |
| RQ-X4-03 | Exibir fonte e timestamp | `source_id`+`source_retrieved_at` visíveis | unit |
| RQ-X4-04 | Comparação campo a campo | estados MATCH/DIFFERENT/SOURCE_MISSING/CURRENT_MISSING/PROTECTED/NOT_COMPARABLE/UNSUPPORTED/ERROR renderizados com badge | unit por estado |
| RQ-X4-05 | Decisão individual | ACCEPT só elegível; REJECT sempre; refresh + `idempotent_replay` | unit + negativo |
| RQ-X4-06 | Bulk | seleção + modal + atomicidade; sem duplicar em replay | unit |
| RQ-X4-07 | Revisão de resultado | resumo aceitos/rejeitados/pendentes | unit |
| RQ-X4-08 | Prepare-update | draft read-only; banner "não gravado"; `write_gate_enabled=false` | unit |
| RQ-X4-09 | Histórico | lista paginada actor-scoped + abrir revisão | unit + paginação |
| RQ-X4-10 | Erros reais | todos os codes da §6 mapeados para mensagens úteis | unit por code |
| RQ-X4-11 | URL/F5 | seção âncora + revisão aberta por deep link | structural |
| RQ-X4-12 | A11y/responsivo | teclado, aria, mobile 1 col, claro/escuro | structural + manual |
| RQ-X4-13 | Help | tooltips + manual/glossário atualizados (feature-help-sync) | structural |
| RQ-X4-14 | Sem escrita ERP | nenhum caminho UI chama POST/PUT supplier | structural grep |

## 10. Estratégia de testes

- **Unit (Vitest):** reducers/mapeadores de estado, label/badge por `comparison_state`/`eligibility`/`decision_state`, body builder das decisões (chave idempotente estável por ação), mapeamento erro→mensagem.
- **Structural (convenção do plugin):** composição da seção, imports do kit, ausência de chamadas diretas api-delpi/BrasilAPI, ausência de `tax_id` integral/QSA renderizado.
- **Integração:** handlers MSW/fixtures dos 7 endpoints; ciclo consulta→decisões→bulk→draft; replay (`idempotent_replay`), 409 revision/idempotency, 410 expired, 429/503.
- **Regressão:** `suppliers.test.ts`, suite MFE completa, build/tsc; sem mudança backend → suites supplies-api não afetadas (re-executar por segurança no S1).

## 11. Plano X4.S1 — menor diff

1. `features/suppliers/enrichment/` (novo módulo MFE): `api.ts` (7 calls via `httpClient`), `types.ts` (DTOs espelhando `_review_view`/`_proposal_view`/`_decision_view`), `stateMachine.ts`, `EnrichmentSection.tsx`, `EnrichmentComparisonTable.tsx`, `EnrichmentHistoryTable.tsx`, `content.ts` (PT-BR §7).
2. Extender `SupplierDetailPage.tsx`: montar `EnrichmentSection` (âncora `#enrichment`), CTA na toolbar/hero.
3. Opcional E13: ação "Enriquecer" por linha → deep link `supplier_detail#enrichment`.
4. `content.ts`/`helpTooltips.ts`/`userManualContent.ts`: sync de ajuda.
5. Testes §10. **Zero mudança**: backend, manifest, rotas, RBAC, migrations, plugin-ui, write gate.

## 12. Referências

- Rotas/DTOs: `supplies-api/app/interfaces/http/routes/supplier_enrichment_routes.py`
- Domínio S1/S2: `supplies-api/app/domain/supplier_enrichment/{models,comparison,review_lifecycle}.py`
- MFE fornecedores: `plugins/supplies/src/features/suppliers/`
- Kit: `plugins/supplies/src/app/suppliesUi.ts` + `shims/plugin-ui.d.ts`
- Decisão provider: `SUPPLIES-ENRICHMENT-01-BRASILAPI-MVP-DECISION-20261022.md`
- Evidência E2E: `../shared-integrations/X3-RUNTIME-EVIDENCE-20261022.md`
