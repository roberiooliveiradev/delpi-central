# ChatAssistantContent — apresentação rica unificada

Documentação da renderização de respostas operacionais no plugin **minha-delpi-chat** (jun/2026). Substitui o antigo `ChatRichPresentation`.

Relacionado: [chat-intelligence-base.md](./chat-intelligence-base.md), [humanized-narrative-stack-jun2026.md](./humanized-narrative-stack-jun2026.md), [playbook-09-apresentacao-rica.md](../roadmap/playbook-09-apresentacao-rica.md), [roadmap apresentação generalizada jun/2026](../roadmap/apresentacao-dados-generalizada-jun2026.md), [playbook 12 — refatoração declarativa](../roadmap/playbook-12-apresentacao-declarativa-refatoracao.md), [changelog multi-rota](../changelog/2026-06-apresentacao-multi-rota-produto.md).

---

## Princípio

| Camada | Responsabilidade |
|--------|------------------|
| **API (chat base)** | Montar `presentation` + visuais secundários, `textPresentation`, `presentationDecision` (o que combinar e em que ordem) |
| **MFE** | `ChatAssistantContent` monta segmentos; **uma rota** ou analyser: narrativa + barra global de formato; **várias rotas** do mesmo produto: seções numeradas com toolbar **por bloco** (ver [Consulta multi-rota](#consulta-multi-rota-mesmo-produto-jun2026)) |

Agentes **não** reimplementam layout; herdam metadata das tools.

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
  → ChatPresentationHumanizedNarrativeService.enrich_metadata
       narrativa fina → panorama/leitura/atenção/conclusão (qualquer action com painéis)
  → ChatPresentationStackOrderService.enrich_metadata
       stackPresentationPlan (ordem narrativa + papéis de tabela por rota)
  → toolCalls[].metadata no turno do chat

MFE: buildAssistantContentSegments(content, toolCalls)
  → (se 2+ rotas /products/… OK, exceto só analyser) buildMultiRouteStackSegments
  → senão resolveAssistantContentLayout (stack | markers | text-only)
  → presentationStackBlueprint: lead → ficha → destaques → tabelas operacionais → árvore/gráfico → pontos
  → ChatAssistantContent: toolbar global OU AssistantContentRouteSection (toolbar por seção)
  → assistantContentRegistry → ChatRichTable | ChatRichTree | ChatRichChart | …
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
| `layoutMode` | `"stack"` quando há **≥ 2** views em `availableViews`; senão `"single"` |
| `visualOrder` | Ordem de empilhamento: texto → tabela → árvore → gráfico → kpi → dashboard |
| `selected` | Formato sugerido (texto, tabela, árvore, tipos de chart) |
| `availableViews` | Todos os formatos que o MFE pode oferecer na barra de troca |

**Deduplicação estrutura × tabela:** quando há árvore da mesma hierarquia (BOM, parents, analyser), tabelas planas equivalentes (`Componentes da estrutura`, lista de pais) são removidas do metadata (`ChatPresentationStructureDedupService`). O formato **Tabela** no analyser mantém roteiro, inspeção e ficha — não a lista plana de componentes. Com `preferredFormat: table` na rota de estrutura, a árvore é suprimida e permanece só a tabela plana.

Serviço: `ChatPresentationDecisionService._build` / `enrich_metadata`.

---

## Modos de layout no MFE

| Modo | Quando | Comportamento |
|------|--------|----------------|
| **stack** | `layoutMode === "stack"` (default em rotas ricas com painéis; ver `ChatPresentationRichStackPolicyService`) | Narrativa intercalada com `stackPresentationPlan` + `humanizedSections`; analyser mantém mockup 1–7; demais rotas usam seções Panorama/Leitura/Atenção/Conclusão. Em stack humanizado, `textPresentation` **não** é compactado e **sem** marcadores `[[table]]`/`[[arvore]]` |
| **markers** | Markdown com `[[tabela]]`, `[[arvore]]`, `[[grafico]]` | Visuais inseridos nas posições dos marcadores |
| **text-only** | Sem visual rico | Só markdown/código |

Arquivos: `assistantContentLayout.ts`, `assistantContentSegments.ts`.

---

## Barra de troca de formato

Quando `resolveAvailableVisualFormatOptions` retorna **≥ 2** opções (e **não** é apresentação multi-rota — ver abaixo):

- Em **stack** (analyser e combinações): exibe narrativa + cada componente nativo com dados (várias tabelas, árvore, gráfico).
- Toolbar de troca (**Completo** / **Texto** / **Tabela** / **Árvore** / **Gráfico**) no topo de `ChatAssistantContent` — filtro global sobre todos os segmentos.
- Leitura vertical intercalada: destaques → roteiro/ficha (tabelas) → pontos de atenção → árvore (ver `ChatRichPresentationTextService.embed_visual_markers_in_markdown` e `assistantContentInterleave.ts`).

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

## Migração desde `ChatRichPresentation`

- **Removido** em jun/2026; não importar em código novo.
- Toggle texto/tabela/gráfico/árvore → `AssistantContentFormatToolbar` dentro de `ChatAssistantContent`.
- Modo `commentary-visual` → `layoutMode: "stack"` + filtro por visual ativo.
- Docs antigas que citam `ChatRichPresentation` devem apontar para este arquivo.
