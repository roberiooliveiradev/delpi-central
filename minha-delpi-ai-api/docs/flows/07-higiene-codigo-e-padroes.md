# 07 — Higiene de código e alinhamento às diretrizes

> Inventário de **código morto removido**, **legado ainda wired** e **dívida fora do padrão**.  
> Critério: só apagar com evidência (zero import em `app/` fora do próprio arquivo + não no pipeline send/stream).  
> Regras Cursor: `schema-first-presentation-delivered`, `centralized-rules-first`, `assistant-content-json`, `clean-architecture-chat-api`.

---

## Removido nesta limpeza (ago/2026)

| Módulo | Motivo |
|--------|--------|
| `chat_assistant_identity_llm_synthesis_service.py` | Stub `POLICY_NAME` sem callers; prompt usa string em `ChatPromptBuilderService` |
| `chat_capabilities_llm_synthesis_service.py` | Idem |
| `external_action_result_presenter_facade_access.py` | `result_presenter_type()` sem callers |
| `chat_presentation_operational_root_service.py` | Só testes; schema-driven não usa |
| `chat_presentation_supplier_display_service.py` | Só testes; fora do pipeline |
| `chat_presentation_tree_meta_caption_service.py` | Só testes; árvore schema-driven não chama |
| `chat_drawing_pdf_embedded_text_service.py` | Alias → `ChatPdfEmbeddedTextService` (canônico já usado) |
| `chat_drawing_revision_cross_check_service.py` | Zero imports em `app/`; lógica inline na orchestration de desenho |
| `chat_api_delpi_response_profile_service.py` | Alias → `ChatOperationalResponseProfileService` (callers já no canônico) |

Testes dedicados dos módulos acima também removidos. Inventário: `docs/architecture/services-inventory-baseline.json` (regenerar com `--write-baseline` após remoções).

---

## Gaps fechados (ataque pós-limpeza)

| Gap | Entrega |
|-----|---------|
| `entityProfiles` × `openapiReplaceableProfileKeys` (8 PAC) | Removidos mapeamentos redundantes; permanece `quality_action_plan_dashboard` → `kpi_dashboard`. Gate `audit_openapi_profile_pruning.py --check` |
| Alias `ChatApiDelpiResponseProfileService` | Módulo removido |
| Callbacks identity/capabilities send×stream | `ChatTurnUseCaseSupportService.bind_*_answer_resolver` |
| PT + `re.compile` em `ChatPresentationStackMarkdownService` | `presenter_content.stackMarkdownMarkers` + `ChatPresentationStackMarkdownContentService` |
| Stack framing OpenAPI (`generic` vs `kpi_series`) | `resolve_effective_profile_key` em section availability / stack markdown |
| `chatCritical` × `profilePresent` (4 entidades) | Incluídas em `profilePresent` (`production_order_detail`, pedidos abertos, proposta) |
| Naming `viewBuildPolicy` + `should_build_views` | Substitui e remove aliases `visualBundle*` |
| `re.compile` lote referência / date range / detail | `reference_resolution.json`, `date_range_vocabulary.patterns`, `interactivity.presentationDetailPatterns` |
| Código de produto duplicado (follow-up/chip/composer) | Usa `ChatProductQueryIntentService.extract_product_code` |
| Path `/stock` em security/summary/follow-up | `ChatPresentationProfileService.has_flag(..., "stock")` |
| `product_query_intent.patterns` + `/analyser` coverage/drawing/turn | JSON + `has_flag(..., "analyser")` |
| Refinement interactivity/stock + direct answers | `has_flag(stock|analyser)` (structure/parents literal OK) |
| Structure comparison, product catalog, drawing metrics/debug | `has_flag(..., "analyser")` |
| Tool context aux/formatter, error classifier, assertiveness | `has_flag(..., "analyser")` |
| HTTP composite timeout | markers JSON **ou** `has_flag(analyser)` |
| `_COMPARE_PREVIOUS_RE` órfão pós-JSON | `ChatReferenceResolutionService.matches_compare_previous` |
| `reason=` PT em seleção/refinement (lote 1) | `selectionReasons` + `platform_tools` + `web_search.selectionReasons` + `stream.activity` |

---

## Já ausente do disco (anti-padrões Playbook 22)

Presenters por entidade (`product_*_presenter`), `ChatPresentationVisualBundleService`, `TableAssemblyService`, `CompositeVisualBuilder`, `HumanizedNarrativeService`, `entity_route_dispatch` — **não existem** em `app/`. Referências em playbooks históricos são documentação, não runtime.

Pipeline canônico (único):

```
ExecuteExternalAction
 → ChatPresentationMetadataPipelineService
 → ChatPresentationApiDeliveredMetadataService
 → ChatSchemaDrivenPresentationService
 → ChatDataInsightEnrichmentService
 → ChatPresentationDecisionService
 → ChatPresentationRenderPipelineService.finalize
```

---

## Em uso, alinhado (não mexer)

| Área | Canônico |
|------|----------|
| Turno | `ChatTurnPreparationService` / `ChatTurnCompletionService` (send + stream) |
| Operacional | `ExternalActionRouteSelectionService` + `ExecuteExternalActionUseCase` |
| Presenters restantes | SQL, KPI chart, operational_response, presenter_content — exceções legítimas |
| Foco operacional | `operationalFocus` + `userContextItems` (não `lastEntities`) |
| Leak de síntese | `ChatLlmSynthesisLeakGuardService` + JSON da família |
| Perfil OpenAPI | `ChatOperationalResponseProfileService` |

---

## Gaps — revisão (ago/2026, pós-`has_flag`)

Critério: **P0** = quebra regra Cursor / risco de regressão; **P1** = dívida acionável no chat base; **P2** = aceitável / documentado; **Won’t** = não atacar.

### Saúde atual (gates)

| Gate | Resultado |
|------|-----------|
| `audit_openapi_profile_pruning.py --check` | OK |
| `audit_service_inventory.py --summary` | **0** módulos domain/application sem ref estática |
| `visualBuilders` / `tableAssembly` em `presentation_profiles.json` | **Ausentes** (runtime limpo) |
| `visualBundlePolicy` em `app/` | **Ausente** (só `viewBuildPolicy`) |
| Pipeline presentation delivered | Único caminho schema-first (ver § acima) |

### Fechado (não reabrir)

- Órfãos stubs/aliases/helpers só-teste (tabela «Removido»).
- `entityProfiles` PAC substituíveis; callbacks send×stream; naming `viewBuildPolicy`.
- Couche principal `"/stock"` / `"/analyser"` → `has_flag` (refinement, drawing, comparison, tool context, coverage, etc.).
- `matches_compare_previous` após migração JSON.

### P1 — próximo ataque (chat base)

| Gap | Evidência | Direção canônica |
|-----|-----------|------------------|
| `reason=` PT hardcoded em seleção/refinement | **Lote 1 fechado** (stock/route/spec/tools/KPI/web/sql recovery) | Restam notas de síntese web (`_internal_product_synthesis_note` etc.) e outros `reason=` técnicos (códigos EN) |
| `re.compile` em serviços de **regra de negócio** (não loader) | Lotes: `chat_conversation_state_service`, `chat_fast_path_service`, `chat_user_memory_durability_service`, `chat_semantic_memory_intent_service`, `chat_email_*`, `chat_user_context_item_service`, `chat_operational_refinement_vocabulary`, `chat_structure_comparison_service` (parsers de BOM), SQL advisors | Mover **padrões/limites** para `assistant/*.json` + loader; **algoritmo** SQL/OCR pode ficar em Python |
| Inferência de segmento com `"/stock"` em texto livre | `chat_operational_refinement_pagination_service._infer_paginated_route_segment` | Preferir `has_flag(path)` nos toolCalls; no `conversation_context` usar registry marker / flag quando o blob for path-like |
| Doc architecture desatualizada | `chat-assistant-content-presentation.md` ainda cita `visualBundlePolicy` | Alinhar a `viewBuildPolicy` |

### P2 — aceitável (não é bug)

| Item | Por quê manter |
|------|----------------|
| Literais `/stock` `/analyser` em **catálogo / skill / capabilities / memory path→tipo** | Vocabulário de path/OpenAPI e markers de intent — fonte de verdade do contrato HTTP, não ramo de apresentação |
| Fallback `or "/stock"` após `OperationalRouteRegistryService.route_path_marker_for_segment("stock")` | Selection/session refinement: marker do registry primeiro; literal só se registry falhar |
| `pathRules` / `contains: "/analyser"` em `presentation_profiles.json` | Declarativo canônico do perfil |
| `compositePathMarkers` JSON (+ fallback Python) | Timeout HTTP declarativo; `has_flag(analyser)` já complementa |
| `DRAWING_ANALYSER_PATH_TOKEN` | Constante de skill; path TOTVS real |
| `stackPlan` / `ChatPresentationStackOrderService` | Só com `layoutMode==stack`; `richStackProfiles: []` — não reexpandir |
| `ChatPresentationRefactorBaselineService` + avisos `visualBuilders` no coverage | Gate histórico Playbook 12; não reintroduzir builders no runtime |
| `kpi_chart_specialized_service` | Ramos por **shape** de dado (exceção legítima com SQL presenter) |
| `re.compile` em `*_content_service` / `*_patterns_service` / vocabulary loaders | Exceção explícita da regra |
| `re.compile` em parsers SQL/PDF/tokenização | Algoritmo, não vocabulário de produto |

### Won’t / fora de escopo desta higiene

| Item | Nota |
|------|------|
| Reescrever playbooks históricos (12/09) que citam `visualBuilders` | Doc de roadmap; runtime já delivered-puro |
| Apagar módulos «large files» do inventário sem análise de fluxo | Inventário lista tamanho, não órfão |
| Migrar **todo** `re.compile` de uma vez | Incremental por domínio (memória → intent → SQL UI hints) |

### Ordem sugerida do próximo lote

1. `reason=` → JSON (`selectionReasons` / turn prep) + testes de content.  
2. Vocabulário `chat_operational_refinement_vocabulary` + pagination stock → flag/registry.  
3. Um domínio de intent/memória (`conversation_state` ou `fast_path`) → JSON.  
4. Sync docs (`viewBuildPolicy`).

---

## Como revalidar órfãos

```bash
cd minha-delpi-ai-api
.venv/bin/python scripts/audit_service_inventory.py --summary
.venv/bin/python scripts/audit_openapi_profile_pruning.py --check
# Regenerar baseline após remoção consciente:
.venv/bin/python scripts/audit_service_inventory.py --write-baseline
```

**Nunca** apagar só porque aparece em «sem ref estática» — validar fluxo send/stream/simulate/skill (playbook 20 §8.5).

---

## Checklist antes de nova remoção

1. Grep zero de import em `app/` (exceto o próprio arquivo)?
2. Pipeline metadata / turn prep / route selection não chama?
3. Teste de regressão do domínio ainda passa sem o módulo?
4. Doc de fluxos / inventário atualizados?
