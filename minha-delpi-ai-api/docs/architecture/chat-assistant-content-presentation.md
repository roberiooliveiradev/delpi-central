# ChatAssistantContent — apresentação rica unificada

Documentação da renderização de respostas operacionais no plugin **minha-delpi-chat** (jun/2026). Substitui o antigo `ChatRichPresentation`.

Relacionado: [chat-intelligence-base.md](./chat-intelligence-base.md), [humanized-narrative-stack-jun2026.md](./humanized-narrative-stack-jun2026.md), [new-api-route-checklist.md](./new-api-route-checklist.md), [playbook-09-apresentacao-rica.md](../roadmap/playbook-09-apresentacao-rica.md), [roadmap apresentação generalizada jun/2026](../roadmap/apresentacao-dados-generalizada-jun2026.md), [playbook 12 — refatoração declarativa](../roadmap/playbook-12-apresentacao-declarativa-refatoracao.md), [changelog multi-rota](../changelog/2026-06-apresentacao-multi-rota-produto.md), [changelog `summary_then_evidence` e modos](../changelog/2026-06-summary-then-evidence-modos-apresentacao.md), [changelog P6 `renderPlan` e modos](../changelog/2026-06-p6-renderplan-modos-apresentacao.md), [changelog viewIntent](../changelog/2026-06-viewintent-apresentacao-automatica.md).

---

## Princípio

| Camada | Responsabilidade |
|--------|------------------|
| **API (chat base)** | Decidir formato, ordem, supressões e narrativa; serializar **somente** o que deve aparecer (`textPresentation`, visuais, `stackPresentationPlan`, `presentationDecision`, **`renderPlan`**) |
| **MFE** | Materializar segmentos a partir do **`renderPlan`** (ou síntese legada); registry, markdown/prosa, streaming; **sem** regras de negócio de apresentação |

**P6 (jun/2026):** contrato fechado em [playbook-13 §8.6](../roadmap/playbook-13-respostas-humanizadas-dados.md#86-p6--mfe-render-only) e [changelog P6 modos](../changelog/2026-06-p6-renderplan-modos-apresentacao.md).

---

## Pipeline

```
execute_external_action
  → ExternalActionResultPresenter (table / chart / tree / text markdown)
  → ExecuteExternalActionUseCase._build_presentation_metadata
       primary = tree | chart | table (prioridade: tree > chart > table)
       tablePresentation / treePresentation / chartPresentation = secundários (se ≠ primary)
       textPresentation = narrativa (analyser, structure, …)
  → ChatPresentationDecisionService.enrich_metadata
       presentationDecision.layoutMode = "stack" | "single"
       presentationDecision.visualOrder = ["text","table","tree","chart",…]
       presentationDecision.availableViews, selected, insight, recommendations
       dataShape.viewIntent (via ChatPresentationDataShapeAnalyzer)
       ChatPresentationViewIntentService — tabela vs gráfico no Automático
  → ChatPresentationHumanizedNarrativeService.enrich_metadata
       narrativa fina → panorama/leitura/atenção/conclusão (qualquer action com painéis)
  → ChatPresentationStackOrderService.enrich_metadata
       stackPresentationPlan (ordem narrativa + papéis de tabela por rota)
  → ChatPresentationRenderPipelineService.finalize(metadata)
       sync_render_contract_for_explicit_session → prune → renderPlan.build
  → toolCalls[].metadata no turno do chat

MFE: buildAssistantContentSegments(content, toolCalls)
  → buildSegmentsFromRenderPlan(metadata) quando renderPlan.version === 1
  → `resolveRenderPlanForExecution` consome só `renderPlan` v1 da API
  → resolveAssistantContentLayout (stack | single | markers)
  → assistantContentRegistry → ChatRichTable | ChatRichTree | …
```

---

## Metadata da tool (`execute_external_action`)

| Campo | Tipo | Uso |
|-------|------|-----|
| `presentation` | objeto | Visual **primário** (geralmente árvore em analyser/structure) |
| `tablePresentation` | objeto | Tabela secundária (ex.: cadastro do produto no analyser) |
| `treePresentation` | objeto | Árvore secundária (quando primário não é tree) |
| `chartPresentation` | objeto | Gráfico secundário (ex.: donut de composição no analyser) |
| `textPresentation` | `{ type: "markdown", markdown, title? }` | Narrativa; fonte do comentário |
| `preferredFormat` | string | Legado + preferência de sessão (`sessionResponseFormat`) |
| `availableFormats` | string[] | Compatível com `availableViews` |
| `presentationDecision` | objeto | Decisão Playbook 09 + layout (abaixo) |
| `stackPresentationPlan` | objeto | Ordem de intercalação no layout stack (abaixo) |
| `renderPlan` | objeto | **P6** — lista ordenada de segmentos (`kind`, `slot`, `source`); MFE render-only |
| `explicitSessionFormat` | string | Formato escolhido na toolbar (`text`, `table`, `tree`, `chart`, `dashboard`, `canvas`) |

### `stackPresentationPlan` (ordem humanizada)

Gerado por `ChatPresentationStackOrderService` a partir do `path` e do markdown autorizado.

**Analyser** (`/analyser`):

1. `lead` — título / escopo  
2. `profileTables` — ficha cadastral (`Produto {código}`)  
3. `highlights` — **Destaques**  
4. `operationalTables` — roteiro, inspeção  
5. `tailVisuals` — árvore (e gráfico, se houver)  
6. `attention` — **Pontos de atenção** (sempre no final)

**Inteligência (API):** `ChatPresentationSectionAvailabilityService` calcula `humanizedSections`, `presentationProfile` e `sectionVisibility` no `stackPresentationPlan` para **todas as rotas ricas** (analyser, estoque, fabril, MP, simulador, precificação, estrutura, …). Rotas sem builder dedicado recebem plano genérico via `ChatPresentationStackMarkdownService.apply_generic_humanized_stack_plan`. Seção sem dado (ex.: inspeção vazia) não entra no plano nem na narrativa; destaques de “ainda não cadastrado” são filtrados no presenter.

`ChatPresentationHumanizedNarrativeService` complementa markdown **fino** antes do stack plan (panorama a partir da tabela profile, leitura a partir de KPI, conclusão orientando painéis). Precificação (`/pricing`) e MP usam narrativa **completa** no presenter dedicado — ver [humanized-narrative-stack-jun2026.md](./humanized-narrative-stack-jun2026.md).

O MFE injeta `stackSection` (só título) e, em seguida, `sectionFraming[id]` da API como **markdown normal** — frase interpretiva que não repete tabela nem bullets. Em **Completo**, insight/recomendação genérico fica oculto quando há seções humanizadas.

Demais rotas usam o mesmo esqueleto com `tableRoleOrder` adaptado (`stock`, `structure`, `guide`, `list`, `sale_pricing`, …). O MFE infere o papel de cada tabela pelo título ou `role` quando o plano não veio no metadata.

### Perfil `summary_then_evidence` e modos de sessão (jun/2026)

Rotas com `stackPlan: "summary_then_evidence"` (`factory_status`, `stock`, status operacionais): a interpretação (`dataAnswer`) vai para a **prosa do chat**; **não** há `storyPresentation` nem `ChatDecisionCard` duplicando o markdown.

| Modo (`explicitSessionFormat`) | API (`textPresentation`) | `layoutMode` | `renderPlan` |
|--------------------------------|--------------------------|--------------|--------------|
| Automático | Prosa compacta; sem embed GFM | `stack` (ricas) ou `single` (simples) | Stack; **sem** `dashboard` |
| Texto | Markdown completo (`should_embed_in_markdown`) | `stack` se ≥2 visões | Markdown + slots do plano |
| Tabela / Árvore / Gráfico / Painel | Lead compacto ou ausente | **`single`** | Um segmento visual `primary` |
| Documento (`canvas`) | Narrativa para lousa | **`single`** | Só markdown |

Detalhes: [changelog `summary_then_evidence`](../changelog/2026-06-summary-then-evidence-modos-apresentacao.md), [changelog P6 modos](../changelog/2026-06-p6-renderplan-modos-apresentacao.md).

### Mockup de referência — `GET /products/{code}/analyser` (Completo)

Pergunta: «me fale do produto 90260149». Ordem: **ficha no início**, **alertas no final**.

| # | Seção | Conteúdo |
|---|--------|----------|
| 1 | Escopo da consulta | Título + linha «Análise integrada do cadastro, roteiro…» |
| 2 | Ficha cadastral | Tabela CAMPO/VALOR (única ficha; não repetir em texto) |
| 3 | Síntese executiva (Destaques) | Bullets após a ficha |
| 4 | Roteiro de produção | Tabela nativa |
| 5 | Plano de inspeção | Tabela nativa (quando a API enviar `inspection`) |
| 6 | Estrutura (BOM) | Árvore (sem tabela plana de componentes junto) |
| 7 | Alertas e divergências | Lista numerada no final |

**Barra de formatos:** Completo = sequência acima; Texto = 1+3+7; Tabela = 2+4+5; Árvore = 6.

**Não exibir:** insight «sem dados suficientes» no topo; ficha repetida em parágrafo; alertas antes da ficha; frase redundante «A árvore mostra a hierarquia…» no corpo quando já há árvore.

### `presentationDecision` (campos de layout)

```json
{
  "selected": "text",
  "fallback": "table",
  "reason": "visão do produto — narrativa com insights antes da ficha tabular",
  "layoutMode": "stack",
  "visualOrder": ["text", "table", "tree", "chart"],
  "availableViews": ["text", "table", "tree", "chart"],
  "insight": "…",
  "chartExplanation": "…",
  "recommendations": [{ "label": "Ver tabela", "query": "…", "reason": "…" }]
}
```

| Campo | Regra |
|-------|--------|
| `layoutMode` | `"single"` — default texto-first e **formatos nativos explícitos** (table/tree/chart/dashboard); `"stack"` — rotas integradas (analyser, fabril auto, modo Texto com ≥2 visões) |
| `visualOrder` | Ordem de empilhamento: texto → tabela → árvore → gráfico → kpi → dashboard |
| `selected` | Formato sugerido (texto, tabela, árvore, tipos de chart) |
| `availableViews` | Formatos oferecidos na toolbar/chips — inclui views **latentes** do perfil mesmo sem slot montado (`visualBundlePolicy: on_demand`) |

**Deduplicação estrutura × tabela:** quando há árvore da mesma hierarquia (BOM, parents, analyser), tabelas planas equivalentes (`Componentes da estrutura`, lista de pais) são removidas do metadata (`ChatPresentationStructureDedupService`). O formato **Tabela** no analyser mantém roteiro, inspeção e ficha — não a lista plana de componentes. Com `preferredFormat: table` na rota de estrutura, a árvore é suprimida e permanece só a tabela plana.

Serviço: `ChatPresentationDecisionService._build` / `enrich_metadata`.

### Modo Automático — `viewIntent` e perfil (jun/2026)

No modo **Automático** (sem `explicitSessionFormat`), a API escolhe o formato antes do MFE renderizar.

**Ordem de prioridade:**

1. Preferência explícita do usuário (toolbar / mensagem)
2. Perfil JSON (`presentation_profiles.json`) — `chartPolicy: skip`, `defaultViewPolicy`
3. `dataShape.viewIntent` — classificação da forma tabular
4. Marcadores de mensagem em `presentation_vocabulary.json` → `automaticScoreMarkers`
5. `presentationDecision.scores` (último recurso)

| `viewIntent` | Significado | Default típico |
|--------------|-------------|----------------|
| `auditable_list` | Várias colunas descritivas (OP, produto, descrição…) | `table` |
| `ranking` | Label + métrica agregada (filial × saldo) | chart |
| `temporal_series` | Data + numérico | `line_chart` |
| `table_only` | Sem métrica chartável | `table` |

Serviços: `ChatPresentationDataShapeAnalyzer`, `ChatPresentationViewIntentService`, `ChatPresentationProfileService`.

**MFE:** render-only — não redecide tabela vs gráfico. Checklist rota nova: [new-api-route-checklist.md](./new-api-route-checklist.md).

---

## Modos de layout no MFE

| Modo | Quando | Comportamento |
|------|--------|---------------|
| **renderPlan** | `renderPlan.version === 1` | Executor mecânico (`renderPlanSegmentBuilder.ts`) — **preferido** |
| **stack** | `layoutMode === "stack"` | Segmentos do plano stack (lead, tabelas, tail) |
| **single** | `layoutMode === "single"` | Um visual nativo ou só markdown (`nativeSingleViewBuilder.ts`) |
| **markers** | Markdown com `[[tabela]]`, `[[arvore]]`, `[[grafico]]` | Legado — posições de marcadores |

Arquivos: `assistantContentLayout.ts`, `assistantContentSegments.ts`, `renderPlanSegmentBuilder.ts`.

---

## Barra de troca de formato

Quando `resolveAvailableVisualFormatOptions` retorna **≥ 2** opções (e **não** é apresentação multi-rota — ver abaixo):

- Em **stack** (analyser e combinações): exibe narrativa + cada componente nativo com dados (várias tabelas, árvore, gráfico).
- Toolbar de troca (**Completo** / **Texto** / **Tabela** / **Árvore** / **Gráfico**) no topo de `ChatAssistantContent` — filtro global sobre todos os segmentos.
- **Texto** (R14): só prosa/lista — não intercala visuais; **Completo** exige `layoutMode: stack` (visão integrada).

Arquivos: `AssistantContentFormatToolbar.tsx`, `assistantContentVisualFormats.ts`.

| Estado visual | CSS / a11y |
|---------------|------------|
| Opção ativa | `mdc-assistant-content__format-toggle-btn--active` + `mdc-rich-chart__toggle-btn--active` |
| Inativa | Opacidade reduzida na barra da seção |
| Acessibilidade | `aria-pressed` no botão selecionado |

Telemetria: `presentation_view_switch` (mesmo evento do antigo toggle).

---

## Consulta multi-rota do mesmo produto (jun/2026)

Perguntas como «**estoque e onde é usado** do produto 10070011» disparam **várias** `execute_external_action` (`/stock`, `/parents`, …). O MFE **não** deve tratar isso como um único stack do analyser nem fundir visuais entre rotas.

Changelog resumido: [`../changelog/2026-06-apresentacao-multi-rota-produto.md`](../changelog/2026-06-apresentacao-multi-rota-produto.md).

### API

| Serviço | Papel |
|---------|--------|
| `ChatProductMultiScopePlanningService` | Extrai escopos da mensagem; `plan_product_scope_fetches` — analyser único só em «completa/integrada» ou 3+ escopos do analyser |
| `ChatCompositeDirectAnswerService` | Markdown único: intro `multiProductRouteIntro` + `### {rótulo}` por rota com corpo **breve** |
| `ChatProductQueryIntentService.format_direct_answer` | `path` opcional; resumo por escopo (`_format_product_scope_brief`) — sem listagem linha a linha no corpo composto |
| `ExternalActionResultPresenter._present_product_stock` | `linhas` = narrativa; `linhas_detalhe` = posições por filial/armazém |
| `ExternalActionResultPresenter.build_text_presentation` | Modo Texto: resumo + seção **Detalhamento por filial e armazém** |

Intro exemplo (i18n `composite.multiProductRouteIntro`):

> Para o produto **10070011**, organizei a resposta em seções: **estoque e onde o item é usado**. Em cada bloco use os controles…

### MFE — estrutura de segmentos

```text
[lead] markdown da intro (antes do primeiro ###)
─── seção 1 ───
stackSection  "1. Estoque"
toolbar       Completo | Texto | Tabela | Gráfico   ← só opções desta rota
sectionFraming / prose breve do composite
table, chart  ← só metadata da tool /stock
─── seção 2 ───
stackSection  "2. Onde o item é usado"
toolbar       …
tree          ← só metadata da tool /parents
```

| Função | Arquivo |
|--------|---------|
| Detecta 2+ rotas | `isMultiRouteProductPresentation` |
| Monta segmentos | `buildMultiRouteStackSegments` |
| Agrupa para render | `groupSegmentsByRouteSections` |
| Render + filtro local | `AssistantContentRouteSection.tsx` |
| Detalhe no modo Texto | `resolveRouteTextDetailMarkdown` |

Regras importantes:

| Regra | Detalhe |
|-------|---------|
| Sem toolbar global | `shouldUsePerSectionFormatToolbar` → `resolveAvailableVisualFormatOptions` vazio |
| Sem título `h3` duplicado | `showTitle` desligado quando `perSectionToolbar` |
| Cabeçalho da seção fixo | `stackSection` + toolbar **fora** de `filterSegmentsByVisualKind` |
| Aviso **Parcial** / cobertura | `dataCoverageNotice` da **tool call da rota** em `AssistantContentRouteCoverage` (não no topo global) |
| Paginação na seção | Botões Anterior/Próxima só no bloco com `pagination` em `metadata` |
| Estoque padrão | `resolveInitialToolbarKindForRoute('stock')` → **Tabela** |
| Texto na seção estoque | Prose breve + `linhas_detalhe` / `textPresentation` injetados só com `activeKind === 'text'` |
| Plano stack | `resolveMultiRouteStackPlan`: `humanizedSections: false` (mockup 1–7 só no analyser) |

Framing por rota — uma frase interpretiva por bloco (`presentation.routeFraming` em `product_operational_content.json`, exposto no MFE por `operationalPresentationContent.ts`). Ver [Conteúdo operacional de produto](./product-operational-content.md).

### O que não confundir

| Cenário | Layout |
|---------|--------|
| `informações completas` / `análise integrada` | 1× `/analyser` → seções humanizadas 1–7, toolbar global em Completo |
| `estoque + onde é usado` | Multi-rota → seções `route-stock`, `route-parents`, toolbar **por seção** |
| `estoque` só | 1 rota → toolbar global (se ≥ 2 formatos), padrão Tabela |

---

## Visão do produto (`/analyser`)

| Aspecto | Implementação |
|---------|----------------|
| Intent | `ChatProductQueryIntent.ANALYSER` para «me fale do produto …» (`ChatProductOverviewIntentService`) |
| Síntese LLM | `should_force_llm_synthesis` — não usar `directAnswer` só com tabela |
| Roteiro | `tablePresentations[]` ou `tablePresentation` = tabela nativa (`_build_product_analyser_guide_table`) |
| Inspeção | `tablePresentations[]` ou `inspectionTablePresentation` = tabela nativa |
| Cadastro | `tablePresentations[]` (última) ou `profileTablePresentation` = ficha Campo/Valor |
| Estrutura / pais | `presentation` ou `treePresentation` = árvore BOM (`/structure`, `/parents`; analyser usa árvore) |
| Estoque | `tablePresentation` + `chartPresentation` (tabela ou gráfico; ver `ChatPresentationRoutePolicyService`) |
| Gráfico | `chartPresentation` = donut por tipo de componente (≥ 2 tipos na estrutura) |
| Texto | Abertura, destaques, **pontos de atenção** (`ChatProductAnalyserDivergenceService`) |
| Policy LLM | `product-overview.md` |

O corpo em markdown **não** deve repetir tabela Campo/Valor (`stripRedundantProfileTableFromMarkdown` no MFE).

---

## Extensão — novo componente visual

1. Definir tipo em `ChatPresentation` (`chatTypes.ts`) e montar no presenter/API.
2. Adicionar kind em `assistantContentTypes.ts` (`AssistantContentSegment`).
3. Registrar renderer: `registerAssistantSegmentRenderer(kind, fn)` em `assistantContentRegistry.tsx`.
4. Incluir kind em `AssistantVisualKind` + `VISUAL_LABELS` em `assistantContentVisualFormats.ts`.
5. Mapear view em `ChatPresentationDecisionService._visual_order_for_stack` se for formato global.

Sem alterar `ChatMessageList` — ele só usa `ChatAssistantContent`.

---

## Arquivos principais (MFE)

| Arquivo | Papel |
|---------|--------|
| `ChatAssistantContent.tsx` | Orquestra chrome, toolbar global ou delega seções multi-rota |
| `AssistantContentRouteSection.tsx` | Toolbar + filtro **por** bloco de rota |
| `presentationMultiRoute.ts` | Stack multi-rota, agrupamento, detalhe texto |
| `operationalPresentationContent.ts` | Títulos e framing de rota (JSON compartilhado com a API) |
| `assistantContentSegments.ts` | `buildAssistantContentSegments`, coleta visuais |
| `assistantContentLayout.ts` | `layoutMode`, ordenação |
| `assistantContentVisualFormats.ts` | Opções de troca, `shouldUsePerSectionFormatToolbar`, filtro |
| `assistantContentRegistry.tsx` | Mapa kind → componente React |
| `AssistantContentChrome.tsx` | Insight, recomendações, paginação |
| `chatPresentation.ts` | Helpers, strip de markdown redundante |

---

## Arquivos principais (API)

| Arquivo | Papel |
|---------|--------|
| `ChatProductMultiScopePlanningService` | Várias rotas `/products/{code}/…` na mesma pergunta |
| `ChatCompositeDirectAnswerService` | Markdown composto + `multiProductRouteIntro` |
| `ChatProductQueryIntentService` | `format_direct_answer(..., path=)` — resumo breve por escopo |
| `ChatExternalActionOrchestrationService` | Orquestra planejamento multi-escopo antes de `select_action` |
| `ExecuteExternalActionUseCase` | Metadata multi-visual; `preferredFormat` texto em analyser |
| `ExternalActionResultPresenter` | Tabelas, árvores, charts; estoque `linhas` + `linhas_detalhe` |
| `ChatPresentationDecisionService` | `layoutMode`, `visualOrder`, `availableViews` |
| `ChatProductAnalyserDivergenceService` | Pontos de atenção confiáveis |
| `ChatProductOverviewIntentService` | Overview → analyser + LLM |
| `app/content/pt-BR/assistant/external_action_responses.json` | `composite.multiProductRouteIntro`, `composite.multiProductCodesIntro` |
| `app/content/pt-BR/assistant/product_operational_content.json` | Escopos, termos plurais, presenter, `presentation.*`, web search — ver [product-operational-content.md](./product-operational-content.md) |

---

## Testes

| Pacote | Arquivos |
|--------|----------|
| API | `test_rich_presentation.py`, `test_external_action_result_presenter_analyser*.py`, `test_chat_product_analyser_divergence_service.py` |
| MFE | `presentationMultiRoute.test.ts`, `assistantContentLayout.test.ts`, `assistantContentVisualFormats.test.ts`, `assistantContentSegments.test.ts`, `chatPresentation.test.ts` |

Build MFE: `npm run build` em `plugins/minha-delpi-chat`.

---

## Desacoplamento narrativa × visual × cobertura (jun/2026)

Regra permanente do repositório: **`presentation-operational-decoupling.mdc`** (`alwaysApply: true`).

Regra: **presenters** montam estrutura visual (`tablePresentation`, `textPresentation` compacto); **interpretação** (destaques, atenção, limitações, incompletude, consolidado) fica no pipeline base.

| Sinal | Módulo canônico | Consumidor MFE |
|-------|-----------------|----------------|
| Resultado incompleto / paginação operacional | `ChatOperationalResultCompletenessService` → `ChatDataCoverageNoticeService` | Banner `metadata.dataCoverageNotice` |
| Refinamento local (agrupamento sobre amostra) | `ChatOperationalGroupBySessionRefinementService` → `sessionDataRefinement` + `sessionAggregateSample` | Ver [session-data-refinement.md](./session-data-refinement.md) |
| Atenção e limitações na prosa | `ChatDataInsightService` → `dataAnswer` / `dataCommentary` | Lead do `renderPlan` (modo Automático) |
| Dica «use a tabela/árvore» | `ChatPresentationVisualUiHintService` → `presentationDecision.recommendations` | Toolbar / chips de formato |
| Insight curto do visual selecionado | `ChatPresentationInsightService.build_with_metadata` (prioriza `dataAnswer`) | Legenda do painel |
| Campos técnicos (`is_complete`, `branch_filter_applied`, `consolidated_across_branches`) | API: `ProductionOperationalSummarySemanticsService` · Chat: `ChatOperationalSummarySemanticsService` + `ChatPresentationOperationalMetadataFieldService` | **Não** entram em KPI, linhas playbook nem markdown |
| Insights por rota (fabril, estoque, pricing, analyser) | `ChatOperationalDataCommentaryService` (+ serviços dedicados) | `dataAnswer` via `ChatDataInsightEnrichmentService` |

### O que os presenters **não** devem mais embutir

- `tableVisualizationHint` / `treeVisualizationHint` em `linhas` ou markdown
- `moreDetailRecords` / `paginatedResult` (cobertura unificada)
- Seções **Destaques** / **Pontos de atenção** duplicando `dataCommentary`
- `presentation.incompleteNotice` ou equivalente só no visual

### Heurística «lista extensa»

`ChatDataInsightService` só emite `largeList` quando **não** há incompletude operacional nem flag `paginated` — evita aviso genérico redundante com `dataCoverageNotice`.

---

## Migração desde `ChatRichPresentation`

- **Removido** em jun/2026; não importar em código novo.
- Toggle texto/tabela/gráfico/árvore → `AssistantContentFormatToolbar` dentro de `ChatAssistantContent`.
- Modo `commentary-visual` → `layoutMode: "stack"` + filtro por visual ativo.
- Docs antigas que citam `ChatRichPresentation` devem apontar para este arquivo.
