# Conteúdo operacional de produto — `product_operational_content.json`

Textos de usuário e **listas de termos** para consultas de produto (intenção, pluralidade, apresentação, estoque, web search) ficam centralizados em um JSON editável, em vez de strings espalhadas no Python/TypeScript.

Relacionado:

- [chat-intelligence-base.md](./chat-intelligence-base.md) — pipeline do chat base
- [chat-assistant-content-presentation.md](./chat-assistant-content-presentation.md) — multi-rota no MFE
- [changelog multi-rota](../changelog/2026-06-apresentacao-multi-rota-produto.md)

---

## Arquivo e loader

| Item | Caminho |
|------|---------|
| Conteúdo PT-BR | `app/content/pt-BR/assistant/product_operational_content.json` |
| Loader | `ChatProductOperationalContentService` (`app/domain/services/chat_product_operational_content_service.py`) |
| Cache | `@lru_cache` — em testes que alteram JSON, usar `invalidate_product_operational_content_cache()` |

API pública do loader (mesmo estilo de `ExternalActionResponseContentService`):

- `get(*path, default="")` — string em caminho aninhado
- `format(*path, **values)` — template com `{placeholders}`
- `list(*path)` — array de termos
- `get_mapping(*path)` — objeto chave → string
- `scope_label_for_scope_key`, `scope_labels_from_api_path`, `composite_short_scope_labels_from_path`
- `join_list_pt(items)` — «A e B» / «A, B e C»

Templates de intro **composta** que usam placeholders específicos continuam em `external_action_responses.json` (`composite.multiProductRouteIntro`, `composite.multiProductCodesIntro`); os **rótulos de escopo** inseridos nesses templates vêm do JSON operacional.

---

## Estrutura do JSON

### `scopes`

Rótulos humanos por escopo e por fragmento de path da API.

| Chave | Uso |
|-------|-----|
| `byScopeKey` | `profile`, `stock`, `structure`, … — planejamento multi-escopo (`ChatProductMultiScopePlanningService._reason_for_scope`) |
| `byPathFragment` | `/stock`, `/parents`, … — intro multi-código (`ChatProductPluralPhrasingService.scope_labels_from_api_path`) |
| `compositeShort` | Rótulos curtos na intro multi-rota (`ChatCompositeDirectAnswerService._build_multi_route_intro`) |

### `listJoin`

Templates para juntar listas em português: `two` (`{first} e {second}`), `many` (`{head}, {last}`).

### `pluralPhrasing`

Enriquecimento de **detecção** sem alterar código.

| Chave | Uso |
|-------|-----|
| `productReferenceTerms` | «desses produtos», «os itens citados», … — contexto com vários produtos |
| `productEntityTerms` | «produto», «itens», … — referência a entidade na mensagem |
| `linkedScopeStems` | Stems para padrão «{escopo} dos produtos» (regex no `ChatProductPluralPhrasingService`) |
| `scopeTerms` | Por escopo (`stock`, `structure`, `sales`, `description`): `terms` + `pluralTerms` com match por **palavra inteira** (evita `descricao` ⊃ `composicao`) |

Consumidores: `ChatProductPluralPhrasingService`, `ChatProductQueryIntentService` (`_looks_like_stock_question`, estrutura, vendas, descrição), `ChatAnalysisIntentService._message_uses_active_context_products`.

### `referencesPreviousProduct`

Termos de follow-up («desses produtos», «produtos acima», …) mesclados em `ChatProductQueryIntentService.references_previous_product` (filtros de filial permanecem no código).

### `presenter`

Textos do `ExternalActionResultPresenter` e correlatos.

| Subseção | Exemplos |
|----------|----------|
| `stock` | Resumo «Consultei o estoque…», linha de detalhe filial/armazém, hint modo Texto |
| `profile` | `nextStepsHint`, mensagens de coleções vazias/com total |
| `analyser` | Título, `scopeIntro` |
| `parents` | Títulos «Onde é usado…» |
| `inspection` | `summaryFallback` |
| `items` | Título genérico de lista |
| `collections.labels` | Rótulos «Roteiro», «Inspeção», … |

### `presentation`

Títulos e **framing** por rota no MFE — **fonte única** API + plugin.

| Chave | Uso |
|-------|-----|
| `routeTitles` | Cabeçalho `1. Estoque — {código}` |
| `routeFraming` | Parágrafo interpretivo abaixo do título da seção |
| `sectionFraming` | Frases do analyser humanizado (`ChatPresentationSectionAvailabilityService`) — `scopeWithCode`, `profile`, `guide`, … |

O MFE importa o mesmo arquivo via `plugins/minha-delpi-chat/src/content/operationalPresentationContent.ts` (`routeTitle`, `routeFraming`, `ProductRouteKey`).

### Web search

Textos de pesquisa web foram movidos para [`assistant/web_search.json`](./assistant-content-catalog.md) (`ChatWebSearchDirectAnswerService`).

### `multiScope` / `composite`

- `multiScope.reasonTemplate` — motivo da action em consulta combinada
- `composite.informedProductFallback` — código substituto na intro quando não há código na mensagem

---

## Fluxo — onde cada texto entra

```text
Mensagem do usuário
    ↓
ChatProductQueryIntentService (+ termos JSON via PluralPhrasing)
    ↓
ChatExternalActionOrchestrationService
    · 1 produto, 2+ escopos → MultiScopePlanning
    · 2+ códigos, mesmo intent → multi_product (STOCK, PARENTS, …)
    ↓
ExecuteExternalAction → ExternalActionResultPresenter (textos presenter.*)
    ↓
ChatCompositeDirectAnswerService
    · intro: external_action_responses.composite.*
    · escopos listados: product_operational_content.scopes
    ↓
MFE ChatAssistantContent
    · títulos/framing: product_operational_content.presentation (import JSON)
```

---

## Cenários cobertos (jun/2026)

### Multi-rota — mesmo produto, vários escopos

Ex.: «estoque e onde é usado do produto 10070011».

- API: várias actions; intro `multiProductRouteIntro`; corpo breve por `###`
- MFE: seções numeradas, toolbar por bloco, aviso Parcial por rota

### Multi-produto — mesmo escopo, vários códigos

Ex.: «estoque dos produtos 10080022, 10080012» ou «onde são usados os produtos …».

- API: intent refinado (plural); uma action por código; intro `multiProductCodesIntro`
- MFE: título de seção com código (`1. Estoque — 10080022`)

### Contexto sem código explícito

Ex.: «estoque» com dois produtos em `userContextItems`.

- `ChatAnalysisIntentService.extract_product_codes_for_action_planning` + termos plural/contexto do JSON

---

## Como enriquecer (checklist)

1. **Novo sinônimo operacional** — adicionar em `pluralPhrasing.scopeTerms.{escopo}.terms` ou `productReferenceTerms`; rodar testes em `test_chat_product_plural_phrasing_service.py` e `test_chat_product_query_intent_service.py`.
2. **Novo rótulo de escopo** — `scopes.byScopeKey` + `byPathFragment` + `compositeShort` se aparecer em intro composta.
3. **Nova frase de estoque/presenter** — `presenter.stock.*`; ajustar `ExternalActionResultPresenter` só se o **formato** dos dados mudar, não o texto.
4. **Novo título/framing no MFE** — `presentation.routeTitles` / `routeFraming`; rebuild `minha-delpi-chat` (import direto do JSON da API).
5. **Intro composta longa** — preferir `external_action_responses.json` (`composite.*`) para parágrafos com tom de assistente; usar `product_operational_content` para **nomes de escopo** e listas.

Não duplicar o mesmo rótulo em três lugares: path fragment → `scopes.byPathFragment`; chave de escopo → `byScopeKey`; UI → `presentation.routeTitles` (podem divergir de propósito: «Estoque» na UI vs «estoque» na intro).

---

## Serviços e arquivos de código

| Serviço / arquivo | Papel |
|-------------------|--------|
| `ChatProductOperationalContentService` | Leitura do JSON |
| `ChatProductPluralPhrasingService` | Plural + labels por path |
| `ChatProductMultiScopePlanningService` | Planejamento 2+ escopos |
| `ChatCompositeDirectAnswerService` | Markdown composto |
| `ChatExternalActionOrchestrationService` | `multi_product`, refinamento de intent |
| `ChatPresentationSectionAvailabilityService` | Framing analyser (`sectionFraming`) |
| `ChatWebSearchDirectAnswerService` | Textos `webSearch.*` |
| `operationalPresentationContent.ts` (MFE) | Bridge para `presentation.*` |

---

## Testes

| Pacote | Arquivo |
|--------|---------|
| API | `test_chat_product_operational_content_service.py` |
| API | `test_chat_product_plural_phrasing_service.py` |
| API | `test_chat_composite_multi_product_codes_intro.py` |
| API | `test_chat_external_action_orchestration_service.py` |
| MFE | `presentationMultiRoute.test.ts` |

```bash
# API (exemplo com Docker)
docker run --rm -v "$(pwd):/app" -w /app python:3.12-slim \
  bash -c "pip install -q -r requirements.txt pytest && \
  pytest tests/unit/domain/services/test_chat_product_operational_content_service.py \
         tests/unit/domain/services/test_chat_product_plural_phrasing_service.py -q"

# MFE
cd plugins/minha-delpi-chat && npm test -- --run presentationMultiRoute && npm run build
```

---

## Histórico

| Data | Entrega |
|------|---------|
| Jun/2026 | Apresentação multi-rota (API + MFE), estoque humanizado, toolbar por seção |
| Jun/2026 | Pluralidade multi-produto (parents, estoque, estrutura, vendas) |
| Jun/2026 | Centralização em `product_operational_content.json` + loader + import no MFE |

Commits de referência na branch `main`: `feat(chat): multi-rota por produto e intenção no plural` e alterações subsequentes de conteúdo JSON.
