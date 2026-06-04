# ChatAssistantContent — apresentação rica unificada

Documentação da renderização de respostas operacionais no plugin **minha-delpi-chat** (jun/2026). Substitui o antigo `ChatRichPresentation`.

Relacionado: [chat-intelligence-base.md](./chat-intelligence-base.md), [playbook-09-apresentacao-rica.md](../roadmap/playbook-09-apresentacao-rica.md).

---

## Princípio

| Camada | Responsabilidade |
|--------|------------------|
| **API (chat base)** | Montar `presentation` + visuais secundários, `textPresentation`, `presentationDecision` (o que combinar e em que ordem) |
| **MFE** | `ChatAssistantContent` monta segmentos, exibe narrativa + **um** visual ativo com barra de troca entre formatos disponíveis |

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
  → ChatPresentationStackOrderService.enrich_metadata
       stackPresentationPlan (ordem narrativa + papéis de tabela por rota)
  → toolCalls[].metadata no turno do chat

MFE: buildAssistantContentSegments(content, toolCalls)
  → resolveAssistantContentLayout (stack | markers | text-only)
  → presentationStackBlueprint: lead → ficha → destaques → tabelas operacionais → árvore/gráfico → pontos
  → ChatAssistantContent filtra visual ativo + AssistantContentFormatToolbar
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

**Inteligência (API):** `ChatPresentationSectionAvailabilityService` calcula `humanizedSections`, `presentationProfile` e `sectionVisibility` no `stackPresentationPlan` — só rota **`/analyser`**. Seção sem dado (ex.: inspeção vazia) não entra no plano nem na narrativa; destaques de “ainda não cadastrado” são filtrados no presenter.

O MFE injeta `stackSection` com título fixo e `sectionIntros[id]` vindo da API (análise curta do bloco — contagens, código, destaques reais; sem textos de mockup). Em **Completo** do analyser, insight/recomendação genérico fica oculto.

Outras rotas usam o mesmo esqueleto com `tableRoleOrder` adaptado (`stock`, `structure`, `guide`, `list`, …). O MFE infere o papel de cada tabela pelo título quando o plano não veio no metadata.

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
| **stack** | `layoutMode === "stack"`, rotas `/analyser`, `/structure`, `/parents`, ou ≥ 2 views | Narrativa intercalada; **analyser** usa `stackPresentationPlan` + seções humanizadas; demais rotas empilham sem cabeçalhos 1–7. Em stack, `textPresentation` compacto **sem** marcadores `[[table]]`/`[[arvore]]` |
| **markers** | Markdown com `[[tabela]]`, `[[arvore]]`, `[[grafico]]` | Visuais inseridos nas posições dos marcadores |
| **text-only** | Sem visual rico | Só markdown/código |

Arquivos: `assistantContentLayout.ts`, `assistantContentSegments.ts`.

---

## Barra de troca de formato

Quando `resolveAvailableVisualFormatOptions` retorna **≥ 2** opções:

- Em **stack** (analyser e combinações): exibe narrativa + cada componente nativo com dados (várias tabelas, árvore, gráfico).
- Toolbar de troca (**Tabela** / **Árvore** / **Gráfico**) só em layout **não-stack** (um visual por vez).
- Leitura vertical intercalada: destaques → roteiro/ficha (tabelas) → pontos de atenção → árvore (ver `ChatRichPresentationTextService.embed_visual_markers_in_markdown` e `assistantContentInterleave.ts`).

Arquivos: `AssistantContentFormatToolbar.tsx`, `assistantContentVisualFormats.ts`.

Telemetria: `presentation_view_switch` (mesmo evento do antigo toggle).

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
| `ChatAssistantContent.tsx` | Orquestra chrome, toolbar, segmentos |
| `assistantContentSegments.ts` | `buildAssistantContentSegments`, coleta visuais |
| `assistantContentLayout.ts` | `layoutMode`, ordenação |
| `assistantContentVisualFormats.ts` | Opções de troca e filtro |
| `assistantContentRegistry.tsx` | Mapa kind → componente React |
| `AssistantContentChrome.tsx` | Insight, recomendações, paginação |
| `chatPresentation.ts` | Helpers, strip de markdown redundante |

---

## Arquivos principais (API)

| Arquivo | Papel |
|---------|--------|
| `ExecuteExternalActionUseCase` | Metadata multi-visual; `preferredFormat` texto em analyser |
| `ExternalActionResultPresenter` | Tabelas, árvores, charts, corpo analyser |
| `ChatPresentationDecisionService` | `layoutMode`, `visualOrder`, `availableViews` |
| `ChatProductAnalyserDivergenceService` | Pontos de atenção confiáveis |
| `ChatProductOverviewIntentService` | Overview → analyser + LLM |

---

## Testes

| Pacote | Arquivos |
|--------|----------|
| API | `test_rich_presentation.py`, `test_external_action_result_presenter_analyser*.py`, `test_chat_product_analyser_divergence_service.py` |
| MFE | `assistantContentLayout.test.ts`, `assistantContentVisualFormats.test.ts`, `assistantContentSegments.test.ts`, `chatPresentation.test.ts` |

Build MFE: `npm run build` em `plugins/minha-delpi-chat`.

---

## Migração desde `ChatRichPresentation`

- **Removido** em jun/2026; não importar em código novo.
- Toggle texto/tabela/gráfico/árvore → `AssistantContentFormatToolbar` dentro de `ChatAssistantContent`.
- Modo `commentary-visual` → `layoutMode: "stack"` + filtro por visual ativo.
- Docs antigas que citam `ChatRichPresentation` devem apontar para este arquivo.
