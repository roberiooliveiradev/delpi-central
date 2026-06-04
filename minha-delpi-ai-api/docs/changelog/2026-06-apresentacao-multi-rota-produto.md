# Changelog — Apresentação multi-rota de produto (jun/2026)

Melhorias no chat operacional quando o usuário pede **dois ou mais escopos** do mesmo produto na mesma pergunta (ex.: «estoque e onde é usado do produto 10070011»), sem usar o analyser integrado.

Documentação de arquitetura:

- [`../architecture/chat-assistant-content-presentation.md`](../architecture/chat-assistant-content-presentation.md) (seção **Consulta multi-rota**)
- [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md)
- [`../architecture/product-operational-content.md`](../architecture/product-operational-content.md) (JSON central + pluralidade)

---

## Problema

| Sintoma | Causa |
|---------|--------|
| Árvore entre tabela de estoque e gráfico | MFE fundia visuais de **todas** as tool calls e ordenava globalmente (`table` → `tree` → `chart`) |
| Toolbar **Completo** no topo afetava tudo | Filtro de formato em `ChatAssistantContent` aplicado a **todos** os segmentos |
| Árvore sumia ao trocar formato no estoque | `showIn` da seção estoque não incluía `text`; toolbar sumia com o cabeçalho da seção |
| Texto inicial técnico («Filial 01, armazém 01: atual 0…») | `linhas` do presenter misturavam resumo e detalhamento; composite repetia listagem no corpo de cada `###` |
| Botões de formato sem destaque visual | Estilo `--active` pouco contrastante no tema escuro |

---

## API (`minha-delpi-ai-api`)

### Planejamento e resposta composta

| Peça | Mudança |
|------|---------|
| `ChatProductMultiScopePlanningService` | 2+ escopos sem frase «completa/integrada» → várias actions (`/stock`, `/parents`, …) em vez de um único `/analyser` |
| `ChatCompositeDirectAnswerService` | Intro humanizada `composite.multiProductRouteIntro` (código + escopos); seções `### {rótulo}` com corpo **breve** por rota |
| `ChatProductQueryIntentService.format_direct_answer` | `MULTI_SCOPE`, `STOCK`, `PARENTS` e rotas operacionais: parágrafo resumido (`_format_product_scope_brief`), sem bullets linha a linha no markdown persistido |
| `ChatActionLabelService` | Títulos `###` em português nas seções compostas |

Chave i18n (`external_action_responses.json`):

```text
composite.multiProductRouteIntro
→ "Para o produto **{code}**, organizei a resposta em seções: **{scopes}**. …"
```

### Presenter — estoque

`ExternalActionResultPresenter._present_product_stock`:

| Campo | Conteúdo |
|-------|----------|
| `linhas` | 1–2 frases narrativas (filiais, totais, disponível) |
| `linhas_detalhe` | Uma linha por posição (`Filial X, armazém Y: atual …`) |

`build_text_presentation` para `/stock`: resumo em `linhas` + bloco **Detalhamento por filial e armazém** só no markdown da aba Texto (`textPresentation`).

---

## MFE (`plugins/minha-delpi-chat`)

### Detecção e montagem

| Arquivo | Função |
|---------|--------|
| `presentationMultiRoute.ts` | `isMultiRouteProductPresentation`, `buildMultiRouteStackSegments`, `groupSegmentsByRouteSections`, `ROUTE_SHOW_IN`, `resolveRouteTextDetailMarkdown` |
| `operationalPresentationContent.ts` | Importa `product_operational_content.json` — `routeTitle`, `routeFraming` |
| `AssistantContentRouteCoverage.tsx` | Aviso Parcial e paginação por rota |
| `assistantContentSegments.ts` | Prioriza stack multi-rota antes do plano humanizado do analyser |
| `presentationStackPlan.ts` | Multi-rota desliga `humanizedSections` |

Ordem por seção (ex.: estoque): **tabela → gráfico**; estrutura/pais: **tabela → árvore**.

### Toolbar por seção

| Regra | Implementação |
|-------|----------------|
| Sem barra global | `resolveAvailableVisualFormatOptions` retorna `[]` quando multi-rota |
| Barra dentro do bloco | `AssistantContentRouteSection` — após o título `1. Estoque`, etc. |
| Cabeçalho sempre visível | Título + toolbar fora do filtro; só o **corpo** é filtrado |
| Padrão estoque | Abre em **Tabela** (não Completo) |
| Modo Texto | Injeta `resolveRouteTextDetailMarkdown` (detalhe da API) |

### UI

- `ChatAssistantContent`: oculta `h3` global duplicado quando há seções por rota.
- `AssistantContentFormatToolbar` + `ChatAssistantContent.css`: classe `mdc-assistant-content__format-toggle-btn--active`, `aria-pressed`.

---

## Vários produtos na mesma pergunta (jun/2026)

Ex.: «onde são usados os produtos **10080022**, **10080012**?»

| Camada | Comportamento |
|--------|----------------|
| `ChatProductQueryIntentService._looks_like_parents_question` | Reconhece «onde são usados», plural **usados/usadas**, «os produtos» |
| `ChatAnalysisIntentService.extract_product_codes_for_action_planning` | Extrai todos os códigos da mensagem |
| `ChatExternalActionOrchestrationService` | `multi_product` → uma action `/parents` (ou estoque/estrutura) **por código** com intent `PARENTS` |
| `ChatCompositeDirectAnswerService` | Intro `multiProductCodesIntro` + seções `###` com rótulo **— {código}** |
| MFE `presentationMultiRoute` | Títulos de seção `1. Onde o item é usado — 10080022` quando há 2+ rotas |

---

## Pluralidade ampliada (jun/2026)

Além de *parents*, a detecção cobre o mesmo padrão para **estoque**, **estrutura**, **vendas** e **descrição**, e follow-ups no plural («desses produtos», «estoque dos produtos X, Y»).

| Peça | Mudança |
|------|---------|
| `ChatProductPluralPhrasingService` | Termos e stems carregados do JSON; match por palavra inteira; padrão «{escopo} dos produtos/itens» |
| `ChatProductQueryIntentService.refine_operational_intent_from_full` | Um único escopo explícito na mensagem refina `FULL` → STOCK/STRUCTURE/PARENTS/… antes do `multi_product` |
| `ChatAnalysisIntentService` | Contexto com vários produtos reconhece parents + termos plurais do JSON |
| `ChatExternalActionOrchestrationService` | `multi_product` para STOCK, STRUCTURE, SALES, PARENTS, … com 2+ códigos |

Frases de validação adicionais:

| Pergunta | Esperado |
|----------|----------|
| `estoque dos produtos 10080022, 10080012` | 2× `/stock`, intent STOCK |
| `estruturas dos produtos 90260077 e 90260088` | 2× estrutura |
| `vendas dos produtos 10080001 e 10080002` | 2× vendas |

---

## Conteúdo centralizado em JSON (jun/2026)

Textos e listas de termos saíram de strings fixas no código para **`product_operational_content.json`**, com loader `ChatProductOperationalContentService`.

| Antes (espalhado) | Depois (JSON) |
|-------------------|---------------|
| Rótulos em `ChatProductPluralPhrasingService`, composite, multi-scope | `scopes.*` |
| `ROUTE_TITLES` / `ROUTE_FRAMING` no TS | `presentation.*` (importado pelo MFE) |
| Resumos de estoque no presenter | `presenter.stock.*` |
| Framing do analyser por seção | `presentation.sectionFraming` |
| Intro web search | `webSearch.*` |

Guia completo: [`../architecture/product-operational-content.md`](../architecture/product-operational-content.md).

## Frases de validação manual

| Pergunta | Esperado |
|----------|----------|
| `estoque e onde é usado do produto 10070011` | Intro humanizada; **1. Estoque** e **2. Onde o item é usado**; toolbars independentes |
| `onde são usados os produtos 10080022, 10080012` | 2× GET `/parents`; intro com os dois códigos; blocos separados por produto |
| `estoque do produto 10070011` | Uma rota; toolbar global ou única seção; foco tabela/gráfico |
| `informações completas do produto 90260149` | 1× `/analyser`; seções humanizadas 1–7 (inalterado) |
| `estrutura e roteiro do produto 90260149` | 2 rotas; sem misturar árvore no bloco de roteiro |

---

## Testes

| Pacote | Arquivos |
|--------|----------|
| API | `test_chat_product_multi_scope_planning_service.py`, `test_chat_product_query_intent_service.py`, `test_chat_product_plural_phrasing_service.py`, `test_chat_product_operational_content_service.py`, `test_chat_composite_multi_product_codes_intro.py`, `test_chat_external_action_orchestration_service.py` |
| MFE | `presentationMultiRoute.test.ts`, `assistantContentVisualFormats.test.ts` |
