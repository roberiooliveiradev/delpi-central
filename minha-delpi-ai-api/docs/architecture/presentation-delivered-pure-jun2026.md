# Apresentação delivered puro — schema-first (jun/2026)

**Status:** vigente — **substitui** o pipeline rico do Playbook 12 para rotas operacionais  
**Público:** backend, MFE, agentes Cursor, revisores de PR  
**North star:** [playbook-22-schema-first-api-actions-jun2026.md](../roadmap/playbook-22-schema-first-api-actions-jun2026.md)

---

## Princípio

Toda resposta de `execute_external_action` passa por **um único caminho**:

```text
ExecuteExternalAction
  → ChatPresentationMetadataPipelineService.build          (delegação fina)
  → ChatPresentationApiDeliveredMetadataService.build      (único ativo)
       → ChatSchemaDrivenPresentationService               (tabela / KPI / chart / árvore / texto)
       → ChatDataInsightEnrichmentService                  (dataAnswer / dataCommentary)
       → ChatPresentationDecisionService                   (Automático)
       → ChatPresentationRenderPipelineService.finalize    (renderPlan mínimo)
  → MFE render-only (chatPresentation.ts)
```

**Proibido** reintroduzir ramo paralelo por rota, presenter por entidade ou stack rico no pipeline de metadata.

---

## O que foi removido (jun/2026)

| Módulo removido | Substituto |
|-----------------|------------|
| `chat_presentation_visual_bundle_service.py` | `ChatSchemaDrivenPresentationService.build_bundle` |
| `chat_presentation_profile_visual_bundle_service.py` | idem |
| `chat_presentation_table_assembly_service.py` | tabela genérica única (`role: generic`) |
| `chat_presentation_humanized_narrative_service.py` | `ChatDataInsightEnrichmentService` + turn completion |
| `chat_presentation_composite_visual_builder.py` | slots schema-driven + `renderPlan` |
| `chat_presentation_entity_route_dispatch_service.py` | `build_presentation` schema-first |
| 21× `*_presenter.py` por entidade | hosts utilitários em `presenters/` |

O ramo legacy (~520 linhas) de `ChatPresentationMetadataPipelineService` foi **eliminado**. O arquivo agora só delega.

---

## Módulos canônicos (usar estes)

| Responsabilidade | Módulo |
|------------------|--------|
| Pipeline metadata | `ChatPresentationApiDeliveredMetadataService` |
| Forma dos dados / slots visuais | `ChatSchemaDrivenPresentationService` |
| Facade presenter | `ExternalActionResultPresenter` → `finish_schema_first_primary` |
| SQL | `ExternalActionSqlPresenter` |
| KPI / chart | `ExternalActionKpiChartPresenter` |
| Tabela genérica | `presentation_table_host_service` + `ChatPresentationOperationalTableService` |
| Comentário operacional | `ChatDataInsightService` → `ChatDataInsightEnrichmentService` |
| Decisão Automático | `ChatPresentationDecisionService` + `ChatPresentationViewIntentService` |
| Formato explícito (toolbar) | `ChatToolContextFormatService` + `ChatPresentationPrimaryViewService` |
| Prosa template vs LLM | `ChatPresentationProseDeliveryService` (turn completion) |
| Perfis / pathRules | `ChatPresentationProfileService` + `presentation_profiles.json` |
| Nova rota HTTP | OpenAPI import + checklist `new-api-route-checklist.md` |

---

## O que NÃO fazer

| Anti-padrão | Por quê |
|-------------|---------|
| Novo `*_presenter.py` por rota/entidade | Usar schema-driven + OpenAPI `meta` / `x-delpi` (Fase D) |
| `visualBuilders`, `tableAssembly`, `textBuilder` no JSON | Removidos do runtime; só débito declarativo a limpar |
| `if "/products/"` ou `if entity ==` em use case / presenter | Roteamento via `ExternalActionRouteSelectionService` |
| Serviço `ChatOperational{RouteName}Service` | Regra por `profileKey` + JSON transversal |
| Stack rico / multi-tabela tier A no pipeline | Uma tabela genérica + `dataAnswer` quando aplicável |
| Fix só no MFE para decisão de formato | `presentationDecision` vem da API |
| Reativar `presentationStrategy: legacy` sem ADR | Legacy foi cortado; exceção exige playbook + testes |

---

## O que fazer (checklist PR)

- [ ] Rota nova exposta via **OpenAPI import** (não registry manual duplicado)?
- [ ] Apresentação sai de `ChatSchemaDrivenPresentationService` (sem presenter dedicado)?
- [ ] Texto PT novo só em `assistant/*.json`?
- [ ] `dataAnswer` / cobertura via serviços transversais (não markdown do presenter)?
- [ ] Teste com fixture **payload real** da API?
- [ ] Nenhum import de módulo removido (grep `visual_bundle`, `table_assembly`, `composite_visual`)?

---

## JSON — estado (jun/2026, Fase 3)

Chaves **removidas** dos perfis `as_delivered` (sem efeito no runtime desde Fase 1):

- `visualBuilders`, `tableAssembly`, `textBuilder`, `textBuildOptions`, `visualBundle`, `compositeVisualSpec`

`entitySets.presentationTableAssemblyEntities` — esvaziado.

Ainda presentes (runtime parcial ou histórico):

- `richStackProfiles` — **vazio**; reservado para perfis `presentationStrategy: legacy` (Fase 3b)
- `visualBundlePolicy`, `humanizedNarrative` — texto-first / prosa no turn completion
- `stackPlans`, `sectionRules` — comentário e markdown embed
- `stackLayoutPolicy: always` em alguns perfis — **ignorado** para auto-stack quando `as_delivered`; stack só com pedido «visão integrada»

Manter e evoluir:

- `entityProfiles`, `pathRules`, `entitySetProfileContracts`
- `chartPolicy`, `viewOrder`, `commentaryProfileKey`
- `defaults.presentationStrategy: as_delivered`

Depreciar na Fase D: perfis por entidade → `x-delpi` no OpenAPI do provider.

---

## Contrato metadata mínimo (MFE)

| Campo | Origem |
|-------|--------|
| `presentation` | primário schema-driven |
| `tablePresentation` / `kpiPresentation` / `chartPresentation` / `treePresentation` | slots auxiliares |
| `dataAnswer` / `dataCommentary` | `ChatDataInsightEnrichmentService` |
| `dataCoverageNotice` | `ChatDataCoverageNoticeService` |
| `presentationDecision` | `ChatPresentationDecisionService` |
| `renderPlan` | `ChatPresentationRenderPipelineService` |
| `availableFormats` / `preferredFormat` | `ChatPresentationApiDeliveredMetadataService` |

`stackPresentationPlan` rico **não** é mais populado pelo pipeline. Vestígios (`tailVisualPolicy: legacy`) serão removidos na Fase 2 de slim do render.

---

## Testes e gates

```bash
cd minha-delpi-ai-api
.venv/bin/python -m pytest tests/unit/application/services/test_chat_presentation_api_delivered_metadata_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_schema_driven_presentation_service.py -q
.venv/bin/python scripts/generate_operational_route_registry.py --check
```

Regressão de intenção: `tests/fixtures/chat_intelligence_regression_cases.py`.

---

## Documentos relacionados

| Documento | Papel |
|---------|-------|
| [playbook-22](../roadmap/playbook-22-schema-first-api-actions-jun2026.md) | North star actions + apresentação |
| [playbook-12](../roadmap/playbook-12-apresentacao-declarativa-refatoracao.md) | **Histórico** — tier A declarativo (concluído) |
| [humanized-narrative-stack-jun2026.md](./humanized-narrative-stack-jun2026.md) | **Histórico** — stack narrativo removido do pipeline |
| [chat-assistant-content-presentation.md](./chat-assistant-content-presentation.md) | Contrato MFE + `renderPlan` (atualizado) |
| [new-api-route-checklist.md](./new-api-route-checklist.md) | Nova rota api-delpi |

---

## Histórico

| Data | Evento |
|------|--------|
| jun/2026 | Playbook 22 Fase C — `ChatPresentationApiDeliveredMetadataService` único caminho |
| jun/2026 | Remoção de 12 módulos legacy + 21 presenters por entidade |
| jun/2026 | `dataAnswer` re-ligado ao caminho as-delivered |
| jun/2026 | Fase 3 — limpeza JSON (`visualBuilders`/`tableAssembly`), gates auditoria, stubs presenter |
