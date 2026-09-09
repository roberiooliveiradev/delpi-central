# Presentation Intelligence

**Status:** vigente (F0–F9) — pipeline de entrega alinhado ao código  
**Escopo:** `minha-delpi-ai-api` presentation pipeline + `plugins/minha-delpi-chat` render-only

## Pipeline de entrega (ordem real)

Slots schema-driven existem **antes** do miolo PI. O composer LLM (shadow/canary) roda **depois** do primeiro `renderPlan`, não no meio do caminho default.

```text
tool payload + responseSchema
→ ChatSchemaDrivenPresentationService
   (slots: table | kpi | chart | tree | text | dashboard)
→ availableFormats / sessionResponseFormat (PrimaryView)
→ FieldNormalization (labels)
→ ChatPresentationDecisionService.enrich_metadata
   (presentationDecision)
→ TitleNormalization + DataInsightEnrichment
→ stack / text-mode (quando aplicável)
→ ChatPresentationRenderPipelineService.finalize
   → StructureDedup
   → PayloadPruning
   → PresentationIntelligenceOrchestrator.apply_before_render_plan  ← miolo PI
   → suppress siblings (pós-PI)
   → ChatPresentationRenderPlanService.build
   → ChatPresentationLlmCompositionService (markers)
→ PresentationSpecComposerApplicationService.finalize_presentation_metadata
   → se PRESENTATION_COMPOSER_SHADOW|CANARY:
        compose(intent, profile, excerpt)  // sem raw rows
        shadow: só presentationComposerShadow
        canary + validation.ok: re-apply PI + rebuild renderPlan
→ prose data-only / stream metadata
→ MFE: executa renderPlan v1 + slots (render-only)
```

### Miolo PI (dentro do orchestrator)

```text
rows dos slots existentes
→ FieldLabelBundle (PT-BR)
→ PresentationDataProfileBuilder
→ PresentationIntentExtractor (userMessage + requestedPresentation)
→ DeterministicIntentBinder → PresentationSpec
→ [opcional] composer_spec se canary authoritative
→ PresentationSpecValidator
→ PresentationSpecCompiler → reescreve slots + selected
→ presentationIntelligence summary
```

## Composer LLM (opcional)

| Item | Valor |
|---|---|
| Serviço | `PresentationSpecComposerApplicationService` |
| Env | `PRESENTATION_COMPOSER_SHADOW=1`, `PRESENTATION_COMPOSER_CANARY=1` |
| Default | determinístico (composer off) |
| Input | intent + profile candidates + excerpt ≤400 — **nunca** rows do payload |
| Shadow | loga proposta; UI continua deterministic |
| Canary | Spec authoritative só se `validation.ok` |

## Owners

| Responsibility | Owner |
|---|---|
| Slots schema-driven | `ChatSchemaDrivenPresentationService` (+ presenters/assemblers) |
| Decision pré-PI | `ChatPresentationDecisionService` |
| Field/data profile | `PresentationDataProfileBuilderService` |
| Labels PT-BR | `ChatFieldLabelResolutionPipelineService` → `FieldLabelBundle` |
| Intent | `PresentationIntentExtractorService` |
| Binding | `PresentationDeterministicIntentBinderService` |
| Validate | `PresentationSpecValidatorService` |
| Compile | `PresentationSpecCompilerService` |
| Orchestrate (domain) | `PresentationIntelligenceOrchestratorService` |
| Render pipeline | `ChatPresentationRenderPipelineService` |
| renderPlan | `ChatPresentationRenderPlanService` |
| Optional LLM | `PresentationSpecComposerApplicationService` |
| Entrega metadata | `ChatPresentationApiDeliveredMetadataService` |
| Axis defaults | API compiled config (`bindingProvenance=COMPILED`); MFE fallback só se não COMPILED |

## Invariants

- Technical field keys never become UI identity (`xAxis=product_code`, not `Produto`).
- Heatmap requires two discriminant dimensions (cardinality > 1); `unit=UN` is never Y.
- MFE does not own translation dictionaries; it consumes `fieldLabels` / `columns[].label`.
- LLM never receives raw payload rows; only profile + candidates + intent.
- `PresentationSpec` is internal — MFE consumes `renderPlan` + materialized slots only.
- Label provenance (`sourceByKey`) uses canonical tokens: `OPENAPI_TITLE`, `METADATA_SCHEMA`, `CANONICAL_VOCABULARY`, `DETERMINISTIC_HUMANIZER`, `LLM_LOCALIZATION`.
- Schema-first: OpenAPI nova sem `x-delpi`/presenter/`if path` continua útil.

## Gaps conhecidos (baseline Composer universal)

Ver evidence `docs/testing/evidence/presentation-composer-universal-baseline.json` e plano de execução em `.cursor/plans/` (estado de tarefa, não autoridade).

Resumo: Spec/`SUPPORTED_VIEWS` sem `dashboard`; compiler materializa sobretudo chart/table (KPI = labels); tree/dashboard/text sem `_apply_*`; três catálogos de cor paralelos.

## Evidence

- `docs/testing/evidence/presentation-intelligence-f0-baseline.json`
- `docs/testing/evidence/presentation-composer-universal-baseline.json` (quando versionado)
- Live smoke: `scripts/smoke_presentation_intelligence_live.py`
  - evidence: `docs/testing/evidence/presentation-intelligence-live.json`
- Contract: `tests/unit/domain/services/test_presentation_preference_token_contract.py`
- Architecture gates: `tests/unit/architecture/test_presentation_intelligence_gates.py`
- Flow: `docs/flows/04-operacional-e-apresentacao.md`
