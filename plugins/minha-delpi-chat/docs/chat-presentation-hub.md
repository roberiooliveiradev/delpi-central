# Hub `chatPresentation.ts` — contrato MFE ↔ metadata da API

> Complementa [`component-structure.md`](./component-structure.md) e [`frontend-refactor-roadmap.md`](./frontend-refactor-roadmap.md) (PR-27–30).

## Por que fica na raiz

`chatPresentation.ts` (~2,4k linhas) é o **único ponto de orquestração** entre `ChatToolCall.metadata` (contrato da API) e as camadas de UI (`message/`, `presentation/`). Não é stub nem re-export legado.

Mover o arquivo inteiro para `message/` ou `presentation/` criaria dependência circular:

- `message/assistantContentLayout.ts` importa readers de decisão/formato.
- `presentation/pipeline/*` importa render plan, pair e dedup.
- O hub importa layout nativo e dedup do pipeline.

**Regra:** lógica de **política/stack/dedup/labels** → `presentation/pipeline/`; lógica de **leitura de metadata + normalização de markdown + pair de apresentações** → permanece no hub até extração por domínio (ver §Extração futura).

## Mapa de responsabilidades (hub)

| Domínio | Exemplos exportados | Consumidores típicos |
|---------|---------------------|----------------------|
| Decisão / formato | `getPresentationDecisionFromToolCalls`, `mapPresentationDecisionToViewFormat`, `isExplicitTextSessionMode` | `message/assistantContentLayout`, `message/assistantContentSegments`, pipeline |
| Render plan / hints | `getRenderPlanFromToolCalls`, `hasRenderPlanContract`, `getPresentationRenderHintsFromToolCalls` | `segmentBuilders/renderPlanSegmentBuilder`, testes P6 |
| Pair / visuais | `getPresentationPairFromToolCalls`, `hasRichPresentation`, `getChartPresentationFromPair` | segment builders, `ChatRich*` |
| Markdown preparado API | `getTextMarkdownFromToolCalls`, `stripRichUiRedundantProseFromMarkdown`, `isApiPreparedMarkdown` | prosa, stack, copy |
| Stack / narrativa | `hasRichStackPresentation`, `resolveStackCommentaryBody`, `resolveCommentaryTextBody` | `stackSegmentBuilder`, interleave |
| Data answer / coverage | `getDataAnswerFromToolCalls`, `getDataCoverageNoticeFromToolCalls` | hub; merge humanizado em `message/humanizedCoverageNotice.ts` |
| Copy / email | `buildAssistantCopyText`, `buildEmailCopyText` | ações do assistente |
| Toggle rich UI | `resolveRichFormatToggles`, `shouldShowRichPresentation` | toolbar, modos |

## O que **não** colocar no hub (já extraído)

| Módulo canônico | Pasta | PR |
|-----------------|-------|-----|
| Stack plan, dedup, metadata policy, labels, telemetry | `presentation/pipeline/presentation*.ts` | 27 |
| Chart axis, agregação, build-from-table | `presentation/pipeline/chart*.ts`, `buildChartPresentationFromTable.ts` | 29 |
| Tree flatten/export, chart payload normalize, explain fallback | `presentation/pipeline/treePresentationUtils.ts`, `chartPresentationNormalize.ts`, `chartExplain.ts` | 30, 32 |
| Segment assembly (stack, render plan, markers) | `presentation/segmentBuilders/` | 25 |
| Prosa / título / markdown stream | `message/assistantProseRendering.ts` | 23 |
| Layout stack vs single, ordem visual | `message/assistantContentLayout.ts` | 20+ |

Barrel do pipeline: `presentation/pipeline/index.ts`.

## Regras de import

```text
message/*          →  ../chatPresentation  (readers + strip helpers)
presentation/*     →  ../chatPresentation  (pair, título, telemetria indireta)
pipeline/*         →  ../../chatPresentation  (render plan, commentary body)
segmentBuilders/*  →  ../../chatPresentation
```

**Proibido:** duplicar `getPresentationDecisionFromToolCalls`, `path.includes` para título de tabela, ou strip de markdown redundante fora do hub / `assistantProseRendering`.

**Gate de regressão:** `presentation/pipeline/presentationLegacyFallbackGate.test.ts` + vocabulário `presentation_vocabulary.json`.

## Extração futura (opcional, por fatia)

Ordem sugerida se o hub crescer de novo — **sem** mover o arquivo monolítico de uma vez:

1. `presentationMetadataReaders.ts` — todos os `get*FromToolCalls` puros (sem markdown).
2. `presentationMarkdownNormalization.ts` — funções `strip*` e compactação client-side.
3. `presentationPairResolver.ts` — `getPresentationPairFromToolCalls`, merge de tabelas.

Cada fatia exige: mover + re-export temporário no hub (deprecate) **ou** atualizar todos os consumidores num PR; teste em `chatPresentation.test.ts` ou suite CI P6.

## Referências cruzadas

| Recurso | Caminho |
|---------|---------|
| Contrato API (metadata) | `minha-delpi-ai-api` → presenters / `presentationDecision` |
| Vocabulário MFE | `src/content/presentation_vocabulary.json` |
| CSS rich (não no hub TS) | [`rich-presentation-css.md`](./rich-presentation-css.md) |
| Testes CI apresentação | `.github/workflows/minha-delpi-ai-api-presentation.yml` |
