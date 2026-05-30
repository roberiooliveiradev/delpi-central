# Conteúdo da API (textos de usuário)

Textos exibidos ao usuário ou usados em respostas diretas da API ficam aqui, separados do código.

## Estrutura

```
app/content/
  pt-BR/
    assistant/     # capacidades, stream SSE, títulos de sessão
    labels/        # rótulos de rotas OpenAPI
    skills/        # catálogo de skills (UI e metadados)
```

Arquivos em `assistant/` usados pela API de chat:

| Arquivo | Uso |
|---------|-----|
| `capabilities.json` | Catálogo de capacidades |
| `column_labels.json` | Colunas e perfis de tabelas operacionais |
| `external_action_responses.json` | Respostas SQL, produção, composite e temporal |
| `identity.json` | Identidade e small talk |
| `operational_parameters.json` | Parâmetros faltantes e ambiguidade de período |
| `small_talk.json` | Respostas conversacionais (8 categorias; padrões editáveis) |
| `utility_answers.json` | Hora, data e dia da semana (resposta direta) |
| `stream.json` | Eventos SSE |

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
