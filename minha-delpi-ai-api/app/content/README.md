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
