# Changelog — P6 `renderPlan` e contrato dos modos de apresentação (jun/2026)

## Contexto

Revisão completa dos **sete modos** do seletor do chat (Automático + seis formatos explícitos), fechando o contrato **API decide → MFE render-only** do Playbook 13 P6.

**Problema principal (Painel):** com `explicitSessionFormat: "dashboard"`, a API promovia o dashboard para o slot `presentation`, esvaziava `dashboardPresentation`, mas o `renderPlan` só olhava slots `*Presentation` — o MFE não montava o painel.

**Problemas correlatos:**

1. Formatos nativos explícitos (Tabela, Árvore, Gráfico, Painel) recebiam `layoutMode: "stack"` quando havia ≥2 visões — o MFE empilhava markdown + visual em vez de **single view**.
2. Modo **Tabela** em rotas de estrutura/BOM perdia a tabela primária após dedup + prune (rich stack preservava árvore; prune removia `presentation` duplicada).
3. Modo **Documento** (`canvas`) não tinha sync de decisão/renderPlan antes do pipeline final.

Relacionado: [playbook-13 §8.6](../roadmap/playbook-13-respostas-humanizadas-dados.md#86-p6--mfe-render-only-próxima-fase), [summary_then_evidence](./2026-06-summary-then-evidence-modos-apresentacao.md), [chat-assistant-content-presentation.md](../architecture/chat-assistant-content-presentation.md).

---

## Mapa UI → API

| Modo (UI) | `sessionResponseFormat` | `explicitSessionFormat` | `layoutMode` | `renderPlan` |
|-----------|-------------------------|-------------------------|--------------|--------------|
| **Automático** | (vazio) | — | `stack` (rotas ricas) ou `single` (texto-first simples) | Stack: markdown + tabelas + tail; **sem** segmento `dashboard` |
| **Texto** | `text` | `text` | `stack` se ≥2 visões | Markdown (+ highlights/attention); visuais auxiliares no payload para toolbar |
| **Tabela** | `table` | `table` | **`single`** | Um segmento `{ kind: "table", source: "presentation" \| "tablePresentations" }` |
| **Árvore** | `tree` | `tree` | **`single`** | Um segmento `{ kind: "tree", source: "presentation" \| "treePresentation" }` |
| **Gráfico** | `chart` | `chart` | **`single`** | Um segmento `{ kind: "chart", … }` |
| **Painel** | `dashboard` | `dashboard` | **`single`** | Um segmento `{ kind: "dashboard", source: "presentation" }` |
| **Documento** | `canvas` | `canvas` | **`single`** | Só `{ kind: "markdown" }` — lousa no MFE |

O composer envia `sessionResponseFormat` no turno; a API grava `explicitSessionFormat` e `preferredFormat` em `execute_external_action` metadata.

---

## Pipeline canônico (fim de `_build_presentation_metadata`)

```text
… ChatPresentationEvidenceFirstLayoutService.compose()
  → ChatPresentationRenderPipelineService.finalize(metadata)
      → ChatPresentationPrimaryViewService.sync_render_contract_for_explicit_session(metadata)
      → ChatPresentationPayloadPruningService.prune(metadata)
      → ChatPresentationRenderPlanService.build(metadata)
```

### `sync_render_contract_for_explicit_session`

| Formato explícito | Ação |
|-------------------|------|
| `table`, `tree`, `chart`, `dashboard`, `kpi` | `selected` = formato; `layoutMode: single`; `visualOrder: [formato]`; `finalize_explicit_native_single_view` |
| `text`, `topics` | `ChatPresentationTextModeService.align_explicit_session_decision` → stack quando há múltiplas visões |
| `canvas` | `selected: canvas`; `layoutMode: single`; `visualOrder: ["canvas", "text"]` |

### `_resolve_visual_source` (renderPlan)

Resolve o slot de dados do segmento visual:

1. `*Presentation` dedicado (`tablePresentation`, …)
2. **`tablePresentations`** (lista) quando `kind === "table"`
3. **`presentation`** quando `presentation.type` coincide com o token

Isso cobre visuais promovidos ao slot primário (ex.: Painel explícito).

---

## Comportamento por modo (detalhe)

### Automático

- Perfil `summary_then_evidence`: prosa compacta; `dashboardPresentation` **omitido** do payload; `tailVisualOrder` = visuais nativos (`tree`, `chart`, `kpi`).
- Rotas simples (ex.: estoque texto-first): `layoutMode: single`, `renderPlan` só markdown.
- `availableViews` mantém formatos latentes para a toolbar — o usuário pode alternar no próximo turno.

### Texto

- Embeds GFM (tabela, árvore, gráfico) **somente** com `explicitSessionFormat: "text"` (`should_embed_in_markdown`).
- Stack com narrativa + visuais auxiliares disponíveis na toolbar; `renderPlan` segue `stackPresentationPlan.narrativeOrder`.

### Tabela / Árvore / Gráfico / Painel (nativos explícitos)

- **`layoutMode: single`** — uma visão nativa por vez; markdown de lead **não** entra no `renderPlan` (exceto Painel com lead curto já compactado na API).
- Prune allowlist inclui `explicitSessionFormat` e `presentationDecision.selected` — visuais latentes permanecem no payload para troca de formato.

### Documento (`canvas`)

- Decisão `selected: canvas`; MFE abre/expande lousa; chat mostra markdown lead via `renderPlan`.

### Estrutura + modo Tabela

- `ChatPresentationStructureDedupService._explicit_table_session` — dedup **não** entra no ramo «árvore vence» quando o usuário escolheu Tabela.
- `ChatPresentationPayloadPruningService._prune_structure_duplicate_tables` — **não** remove `presentation` tipo tabela hierárquica quando sessão explícita é Tabela.

---

## Contrato `renderPlan` v1

```json
{
  "renderPlan": {
    "version": 1,
    "layoutMode": "single",
    "segments": [
      { "kind": "dashboard", "slot": "primary", "source": "presentation" }
    ]
  }
}
```

| `layoutMode` | Origem dos segmentos |
|--------------|----------------------|
| `stack` | `_stack_segments` — `narrativeOrder` + `tailVisualOrder` |
| `single` | `_single_view_segments` — visual nativo selecionado ou markdown (texto/canvas) |

Campos auxiliares: `stackPresentationPlan.renderHints` (`suppressedKinds`, `textRenderMode`, `tailVisualPolicy`).

---

## Módulos alterados (API)

| Serviço | Responsabilidade |
|---------|------------------|
| `ChatPresentationRenderPipelineService` | `finalize()` — sync + prune + renderPlan |
| `ChatPresentationPrimaryViewService` | `sync_render_contract_for_explicit_session` |
| `ChatPresentationRenderPlanService` | `_resolve_visual_source`, canvas single, tablePresentations |
| `ChatPresentationPayloadPruningService` | Allowlist com formato explícito; preserve table primary |
| `ChatPresentationStructureDedupService` | `_explicit_table_session`; dedup não anula Tabela explícita |
| `ChatPresentationTextModeService` | Nativos explícitos → `single` (não stack) |

## MFE (render-only)

| Módulo | Papel |
|--------|-------|
| `renderPlanSegmentBuilder.ts` | Executa `renderPlan.segments` mecanicamente |
| `nativeSingleViewBuilder.ts` | Layout `single` a partir do plano |
| `visualSegmentCollector.ts` | Filtra por `isRenderPlanVisualKindAllowed` |
| `assistantContentSegments.ts` | Orquestrador — prioriza `renderPlan` quando presente |

Sem re-decisão de modo de sessão no frontend.

---

## Testes de regressão

| Pacote | Arquivo | Cobertura |
|--------|---------|-----------|
| API | `test_presentation_render_contract.py` | Prune, renderPlan stack/single, dashboard via `presentation`, modos explícitos |
| API | `test_presentation_session_format_respected.py` | `sessionResponseFormat` → primary + `layoutMode` |
| API | `test_chat_presentation_structure_dedup_service.py` | Rich stack + Tabela preferida; Tabela explícita |
| API | `test_presentation_response_quality.py` | Painel explícito fabril |
| API | `test_presentation_mfe_parity.py` | Contrato JSON ↔ segmentos esperados |
| MFE | `renderPlanSegmentBuilder.test.ts` | Executor do plano |
| MFE | `visualSegmentCollector.test.ts` | Allowlist / renderPlan |

Fixtures tier A (`presentation_vocabulary.json` → `tierAPipelineCases`) atualizadas para P6: dashboard omitido no auto fabril; `layoutMode: single` em rotas texto-first.

---

## Validação manual

1. Nova conversa; produto `90262404`; pergunta status fabril filial 01.
2. **Automático:** prosa + tabelas + árvore/gráfico; **sem** painel integrado.
3. **Painel:** lead curto + dashboard único (`renderPlan` com `kind: dashboard`, `source: presentation`).
4. **Tabela / Árvore / Gráfico:** uma visão nativa por vez (sem stack misto).
5. **Texto:** markdown completo; toolbar ainda permite alternar formato.
6. **Documento:** narrativa na lousa.

Rebuild containers (dev):

```bash
docker compose -f infra/docker-compose.dev.yml --profile chat build minha-delpi-ai-api minha-delpi-chat
docker compose -f infra/docker-compose.dev.yml --profile chat up -d --force-recreate minha-delpi-ai-api minha-delpi-chat
```

Hard refresh no browser (`Ctrl+Shift+R`) após recriar o MFE.

---

## Referências cruzadas

- Gate CI: `.github/workflows/minha-delpi-ai-api-presentation.yml`
- Homologação amostral: [`presentation-homologation-jun2026.md`](../testing/presentation-homologation-jun2026.md)
- Baseline Playbook 12: `docs/architecture/presentation-refactor-baseline-jun2026.json`
