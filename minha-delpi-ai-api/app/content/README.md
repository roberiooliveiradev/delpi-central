# Conteúdo da API (textos de usuário)

Textos exibidos ao usuário ou usados em respostas diretas da API ficam aqui, separados do código.

## Estrutura

```
app/content/
  pt-BR/
    assistant/     # capacidades, stream SSE, títulos de sessão, utility, small talk
    labels/        # rótulos PT-BR das rotas OpenAPI (api-delpi)
    skills/        # catálogo de skills (UI e metadados)
```

Arquivos em `assistant/` usados pela API de chat:

| Arquivo | Uso |
|---------|-----|
| `capabilities.json` | Catálogo de capacidades, `pathRules` api-delpi e detecção operacional (`detection.operationalQueryPatterns`, `suppliesKpiTerms`, …) |
| `api_route_domains.json` | Domínios de rota operacional (`product`, `department_kpi`, `supplies_kpi`, …) e `parameterStrategy` para `ExternalActionRouteSelectionService` |
| `attachments.json` | Welcome de anexo, preview, arquivo extenso, chips de follow-up e ambiguidade da lousa (`ChatAttachmentContentService`) |
| `smoke_e2e_scenarios.json` | Perguntas e marcadores dos smokes E2E (`operational_mixed`, `empresa_kpi`) |
| `column_labels.json` | Colunas e perfis de tabelas operacionais |
| `external_action_responses.json` | Respostas SQL, produção, composite e temporal |
| `product_operational_content.json` | Escopos, termos plurais, textos de presenter, framing MFE/API — doc: [`docs/architecture/product-operational-content.md`](../docs/architecture/product-operational-content.md) |
| `presenter_content.json` | Títulos por rota/KPI e trechos de markdown do presenter |
| `sql_execution_errors.json` | Ponte erros SQL → `error_handling.types` |
| `data_coverage.json` | Avisos de cobertura parcial (paginação, profundidade, SQL) |
| `structure_comparison.json` | Comparação de estrutura entre produtos |
| `memory_ux.json` | Textos de memória de sessão |
| `web_search.json` | Pesquisa web (resposta direta e marcadores) |

Catálogo completo: [`docs/architecture/assistant-content-catalog.md`](../docs/architecture/assistant-content-catalog.md).

Loader genérico: `ChatAssistantContentService` (`app/domain/services/chat_assistant_content_service.py`).
| `identity.json` | Identidade e small talk |
| `operational_parameters.json` | Parâmetros faltantes e ambiguidade de período |
| `small_talk.json` | Respostas conversacionais (8 categorias; padrões editáveis) |
| `utility_answers.json` | Hora, data, dia da semana e ano (resposta direta) |
| `stream.json` | Eventos SSE, status de streaming e títulos de sessão |

Arquivos em `labels/`:

| Arquivo | Uso |
|---------|-----|
| `api_paths.json` | ~84 rotas reais do **api-delpi** → rótulos PT em tool calls e capacidades |

**Typos:** padrões em JSON são comparados após `ChatMessageNormalizationService.normalize_for_matching` (estoque, filial, hora, saudações, KPIs). Novos typos operacionais → serviço Python; typos de frases utilitárias/small talk → JSON e/ou normalização.

Políticas longas para o LLM continuam em `app/domain/prompt_policies/*.md`.

## Convenção JSON vs MD

| Formato | Quando usar |
|---------|-------------|
| **JSON** | Listas, mapas, templates com placeholders (`{agent_name}`), detecção de frases, catálogos |
| **MD** | Instruções longas para o modelo (policies em `prompt_policies/`) |

## Locale

Padrão: `pt-BR`. Novos idiomas = pasta irmã (`en-US/`, …) com a mesma árvore.

## Loader

`ContentService` (`app/infrastructure/content/content_service.py`) lê e cacheia os arquivos.
Serviços de aplicação não devem embutir cópias longas desses textos.
