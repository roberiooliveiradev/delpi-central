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
| Naming `viewBuildPolicy` + `should_build_views` | Substitui `visualBundlePolicy` / `should_build_visual_bundle` (aliases mantidos) |
| `re.compile` lote referência / date range / detail | `reference_resolution.json`, `date_range_vocabulary.patterns`, `interactivity.presentationDetailPatterns` |

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

## Em uso, fora do padrão ideal (dívida restante)

| Item | Status | Direção |
|------|--------|---------|
| `stackPlan` / `ChatPresentationStackOrderService` | Wired só se `layoutMode==stack`; `richStackProfiles: []` | Manter sob demanda; não reexpandir stack rico |
| `re.compile` remanescente em outros `chat_*_service.py` | Parcial (lote referência/date/detail feito) | Continuar migração incremental |
| `if "/stock"` / `"/analyser"` espalhados | Refinement / coverage | Preferir `profileKey` + JSON |
| `kpi_chart_specialized_service` ramos por entidade | Acoplamento residual no host KPI | Absorver em schema-driven quando couber |
| `ChatPresentationRefactorBaselineService` | Gate Playbook 12 histórico | Manter enquanto CI/scripts dependem |
| Aliases `visual_bundle_*` | Compat | Remover em PR futuro após grep zero |

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
