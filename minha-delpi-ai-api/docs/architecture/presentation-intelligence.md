# Presentation Intelligence

**Status:** vigente (F0–F9)  
**Escopo:** `minha-delpi-ai-api` presentation pipeline + `plugins/minha-delpi-chat` render-only

## Pipeline

```text
payload + responseSchema
→ PresentationDataProfileBuilder
→ FieldLabelBundle (PT-BR)
→ PresentationIntent
→ DeterministicIntentBinder → PresentationSpec
→ PresentationSpecValidator
→ PresentationSpecCompiler
→ presentationDecision + slot configs
→ renderPlan
→ MFE render-only
```

Optional LLM composer (shadow/canary) lives in application:

- `PresentationSpecComposerApplicationService`
- env: `PRESENTATION_COMPOSER_SHADOW=1`, `PRESENTATION_COMPOSER_CANARY=1`
- default path remains deterministic; canary is authoritative only with trigger policy + flag

## Owners

| Responsibility | Owner |
|---|---|
| Field/data profile | `PresentationDataProfileBuilderService` |
| Labels PT-BR | `ChatFieldLabelResolutionPipelineService` → `FieldLabelBundle` |
| Intent | `PresentationIntentExtractorService` |
| Binding | `PresentationDeterministicIntentBinderService` |
| Validate | `PresentationSpecValidatorService` |
| Compile | `PresentationSpecCompilerService` |
| Orchestrate (domain) | `PresentationIntelligenceOrchestratorService` |
| Optional LLM | `PresentationSpecComposerApplicationService` |
| Axis defaults | API compiled config (`bindingProvenance=COMPILED`); MFE fallback only |
| renderPlan | `ChatPresentationRenderPlanService` |

## Invariants

- Technical field keys never become UI identity (`xAxis=product_code`, not `Produto`).
- Heatmap requires two discriminant dimensions (cardinality > 1); `unit=UN` is never Y.
- MFE does not own translation dictionaries; it consumes `fieldLabels` / `columns[].label`.
- LLM never receives raw payload rows; only profile + candidates + intent.
- `PresentationSpec` is internal — MFE consumes `renderPlan` + materialized slots only.
- Label provenance (`sourceByKey`) uses canonical tokens: `OPENAPI_TITLE`, `METADATA_SCHEMA`, `CANONICAL_VOCABULARY`, `DETERMINISTIC_HUMANIZER`, `LLM_LOCALIZATION`.

## Evidence

- `docs/testing/evidence/presentation-intelligence-f0-baseline.json`
- Contract: `tests/unit/domain/services/test_presentation_preference_token_contract.py`
- Architecture gates: `tests/unit/architecture/test_presentation_intelligence_gates.py`
- Flow: `docs/flows/04-operacional-e-apresentacao.md`
