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
| `capabilities.json` | Catálogo de capacidades e `pathRules` api-delpi |
| `column_labels.json` | Colunas e perfis de tabelas operacionais |
| `external_action_responses.json` | Respostas SQL, produção, composite e temporal |
| `product_operational_content.json` | Escopos, termos plurais, textos de presenter, framing MFE/API, web search — doc: [`docs/architecture/product-operational-content.md`](../docs/architecture/product-operational-content.md) |
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
