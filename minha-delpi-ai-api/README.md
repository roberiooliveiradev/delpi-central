# Minha DELPI AI API

Backend Flask do **Minha DELPI Chat**: conversas, RAG, agentes, tools, conhecimento global e painel administrativo.

## Documentação

| Área | Caminho |
|------|---------|
| **API (referência completa)** | [docs/api/README.md](docs/api/README.md) |
| Deploy e migrations | [docs/api/09-deploy-migrations-schema.md](docs/api/09-deploy-migrations-schema.md) |
| Roadmap admin (itens 1–15) | [docs/roadmap/admin-minha-delpi-chat.md](docs/roadmap/admin-minha-delpi-chat.md) |
| Gestão de agentes (ondas 1–7) | [docs/roadmap/agentes-gestao-melhorias.md](docs/roadmap/agentes-gestao-melhorias.md) |
| Inteligência do chat (ondas 1–5) | [docs/roadmap/README.md](docs/roadmap/README.md) |
| Melhorias futuras (fechadas) | [docs/roadmap/melhorias-futuras.md](docs/roadmap/melhorias-futuras.md) |
| Plugin (UI) | [../plugins/minha-delpi-chat/README.md](../plugins/minha-delpi-chat/README.md) |

## Base URL (via gateway)

```text
/apps/minha-delpi-ai/api
```

## Requisitos

- Python 3.12+
- PostgreSQL 15+ com extensão **pgvector**
- Keycloak + Core API (JWT e permissões)
- Ollama ou vLLM (conforme `LLM_PROVIDER`)

## Desenvolvimento local

```bash
cd minha-delpi-ai-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Defina `DATABASE_URL` antes de subir o Flask ou rodar migrations (valores em `infra/.env`, host local na porta `5433`):

```bash
set -a && source ../infra/.env && set +a
export DATABASE_URL="postgresql+psycopg://${PLUGINS_DB_USER}:${PLUGINS_DB_PASSWORD}@localhost:5433/${PLUGINS_DB_NAME}"
```

```bash
flask --app app.main:app db upgrade
flask --app app.main:app run --debug
```

Alternativa recomendada com Docker: ver [docs/api/09-deploy-migrations-schema.md](docs/api/09-deploy-migrations-schema.md).

## Estrutura do código

```text
app/
  application/     # use cases e serviços
  domain/          # entidades, ports, exceções
  infrastructure/  # DB, gateways, embeddings
  interfaces/http/ # rotas Flask
  composition/     # factories (DI)
migrations/        # Alembic
docs/              # documentação técnica
```

## Funcionalidades principais

- Chat com histórico, streaming SSE, anexos e artefatos
- RAG documental (pgvector) com fontes na resposta; RAG híbrido, rerank e loop agentic (configurável)
- **Agentes** com instruções, compartilhamento, stats, duplicate/export/import, fontes e actions OpenAPI por agente
- **Projetos** com instruções, agente padrão e compartilhamento
- Base global de conhecimento com pipeline de ingestão
- Painel admin: diretrizes, métricas, auditoria, simulação, avaliações, segurança, especialização de agentes
- Feedback do usuário (thumbs) nas respostas do assistente
- Busca de usuários no diretório (core-api) para compartilhar agentes e projetos

## Variáveis de ambiente relevantes

| Variável | Descrição |
|----------|-----------|
| `DATABASE_URL` | Conexão PostgreSQL (obrigatória) |
| `LLM_PROVIDER` | `ollama` ou `vllm` |
| `LLM_COST_TABLE_JSON` | Tabela de custo fallback (env) |
| `RAG_ASSERTIVENESS_MIN_SCORE` | Limiar de assertividade nos testes RAG (admin) |
| `RAG_CONTEXT_MIN_SCORE` | Score mínimo de chunk no contexto do chat (default = assertividade) |
| `CHAT_ATTACHMENT_CONTEXT_*` | Injeção inline de texto de anexos no prompt |
| `EXTERNAL_ACTION_SEMANTIC_*` | Ranking semântico de actions OpenAPI |
| `CHAT_TOOL_ROUTER_*` | Router LLM para tools/actions |
| `CHAT_HISTORY_SUMMARY_*` | Resumo de histórico longo no prompt |
| `EXTERNAL_ACTION_EMBEDDING_ON_IMPORT` | Gera embedding ao importar OpenAPI |
| `CHAT_RAG_HYBRID_*` | RAG híbrido vetor + keyword |
| `EMBEDDING_CACHE_*` | Cache em memória de embeddings |
| `CHAT_AGENTIC_LOOP_*` | Loop agentic de tools (default desligado) |
| `KNOWLEDGE_SEMANTIC_DEDUP_*` | Deduplicação semântica na pré-visualização |
| `RESPONSE_EVALUATION_LLM_SUGGESTIONS_ENABLED` | Sugestões LLM nas avaliações |
| `CHAT_INPUT_SECURITY_*` | Sanitização e anti prompt-injection |

Lista completa: `app/infrastructure/config/settings.py` e `infra/docker-compose.dev.yml`.

## Testes

```bash
pytest tests/unit -q
```
