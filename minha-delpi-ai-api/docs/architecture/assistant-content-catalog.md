# Catálogo de conteúdo do assistente

**Status:** vigente  
**Regra Cursor:** `.cursor/rules/assistant-content-json.mdc`

## Princípio

`app/content/pt-BR/assistant/*.json` contém **linguagem, UX, vocabulário, thresholds e policies transversais**.

Não é catálogo técnico de APIs.

```text
conteúdo linguístico/configurável → assistant/*.json
contrato técnico de Actions       → OpenAPI + Action Catalog
```

## Loader canônico

`ChatAssistantContentService` e wrappers especializados carregam conteúdo sem espalhar strings/configuração por serviços de domínio.

Operações típicas: `get`, `format`, `list`, `get_mapping` e `get_node`.

Wrappers podem existir quando agregam API semântica estável para um domínio de conteúdo.

## O que pertence aos bundles JSON

| Categoria | Exemplos |
|-----------|----------|
| Copy PT-BR | títulos, mensagens, erros, activities |
| Vocabulário corporativo | aliases, sinônimos, termos internos |
| Regex configurável | OCR, safety, intent lexical |
| Thresholds/caps | limites de contexto, score, paginação UX |
| Policies transversais | fallback, confirmação, comportamento UX |
| Presentation hints | labels/perfis opcionais |
| Prompt/config LLM | templates e limites não secretos |

## O que não pertence aos bundles JSON

Não duplicar fatos já presentes no OpenAPI/Action Catalog:

```text
path
operationId
HTTP method
parameters
required
type/enum/format
request body schema
response schema
technical summary/description
```

Também não criar configuração técnica por endpoint para ensinar routing:

```text
pathMarkers
operationIdMarkers
routeSegment
parameterStrategy
manual endpoint priority
provider selector
```

## Bundles principais

A lista abaixo é por **responsabilidade de conteúdo**, não por endpoint.

| Bundle | Responsabilidade |
|--------|------------------|
| `clarification_policy.json` | clarify material vs discoverable |
| `turn_understanding.json` | configuração da decomposição do turno |
| `conversational_intelligence.json` | flags/config de inteligência conversacional |
| `capability_registry.json` | linguagem/config de capabilities, sem replicar contrato de Actions |
| `response_modes.json` | modos fast/normal/thinker, budgets e alvos |
| `turn_analysis.json` | schema/prompt/config de análise do turno |
| `turn_grounding.json` | caps/statuses de grounding |
| `follow_up_turn.json` | linguagem/policies de follow-up |
| `intent_router.json` | vocabulário/config transversal do router |
| `unclear_requests.json` | mensagens/chips de ambiguidade |
| `error_handling.json` | erros recuperáveis e UX |
| `llm_synthesis_delivery.json` | entrega/safety de síntese |
| `presentation_prose_delivery.json` | prosa da apresentação |
| `presentation_profiles.json` | enriquecimento visual opcional |
| `column_labels.json` | labels de UI |
| `stream.json` | textos/activity SSE |
| `web_search.json` | configuração/UX de web search |
| `document_vision.json` | OCR/visão documental |
| `drawing_validation.json` / `drawing_stamp.json` | regras/config da skill de desenho |
| `memory_intent.json` / `memory_ux.json` | comportamento/UX de memória |
| `capabilities.json` | catálogo UX de capacidades disponíveis |

A existência de um bundle não autoriza duplicar schema técnico de uma Action.

## Actions OpenAPI

Discovery/selection segue:

```text
OpenAPI importado
→ Action Catalog/index
→ allowed actions
→ retrieval
→ planner
→ OpenAPI validator
```

JSON pode enriquecer linguagem corporativa ou policy transversal, mas não pode ser condição para uma API externa ser plugável.

## Regex e thresholds

Quando regex/threshold é configuração:

```text
JSON
→ loader canônico
→ serviço aplica algoritmo
```

Evitar `re.compile`, listas de sinônimos e números mágicos dispersos em domain/application quando são editáveis/configuráveis.

## Presentation

Presentation hints podem viver em JSON, porém:

- fallback schema-driven é obrigatório;
- profile dedicado não é requisito para Action nova;
- MFE renderiza `renderPlan`, não redefine regra de negócio.

## Checklist para nova chave/bundle

1. A responsabilidade já existe em algum bundle?
2. É linguagem/config/policy ou contrato técnico?
3. Se for contrato técnico, deve ir para OpenAPI/importer/Action Catalog.
4. Se for conteúdo, usar loader canônico.
5. Evitar duplicação entre bundles.
6. Adicionar teste do loader/comportamento.
7. Se afetar inteligência, executar protocolo R1–R11.

## Anti-padrões

- endpoint novo → nova entrada técnica no JSON;
- path/opId/args copiados do OpenAPI;
- regex criada só para frase de fixture;
- provider name usado como ranking manual;
- policy de segurança escondida apenas em prompt;
- string PT-BR duplicada em vários serviços;
- hardcode Python migrado para hardcode JSON para passar CI.

## Referências

- [`chat-intelligence-base.md`](./chat-intelligence-base.md)
- [`new-api-route-checklist.md`](./new-api-route-checklist.md)
- [`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md)
- `.cursor/rules/assistant-content-json.mdc`
- `.cursor/rules/openapi-first-universal-tool-routing.mdc`
