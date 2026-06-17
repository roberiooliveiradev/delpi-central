# Minha DELPI AI API

Backend Flask do **Minha DELPI Chat**: conversas, RAG, agentes, tools, conhecimento global e painel administrativo.

## Documentação

**Entrada principal:** [`docs/README.md`](docs/README.md)

| Área | Caminho |
|------|---------|
| **Índice completo** | [docs/README.md](docs/README.md) |
| **Guia do desenvolvedor** | [docs/development/guia-desenvolvimento.md](docs/development/guia-desenvolvimento.md) |
| **Arquitetura (pipeline)** | [docs/architecture/chat-intelligence-base.md](docs/architecture/chat-intelligence-base.md) |
| **Nova rota api-delpi** | [docs/architecture/new-api-route-checklist.md](docs/architecture/new-api-route-checklist.md) |
| **API HTTP (endpoints)** | [docs/api/README.md](docs/api/README.md) |
| **Testes e smokes** | [docs/testing/README.md](docs/testing/README.md) |
| **Conhecimento RAG** | [docs/knowledge/README.md](docs/knowledge/README.md) |
| **Roadmap** | [docs/roadmap/README.md](docs/roadmap/README.md) |
| Plugin (UI) | [../plugins/minha-delpi-chat/README.md](../plugins/minha-delpi-chat/README.md) |
| Visão plataforma | [../docs/08-plugins/minha-delpi-chat/documentacao-tecnica.md](../docs/08-plugins/minha-delpi-chat/documentacao-tecnica.md) |

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

Com Docker, migrations rodam no boot do container (`docker-entrypoint.sh`). Ver [docs/api/09-deploy-migrations-schema.md](docs/api/09-deploy-migrations-schema.md).

## Estrutura do código

```text
app/
  interfaces/http/routes/   # Rotas Flask (handlers finos)
  composition/              # make_* — DI / composition root
  application/              # Use cases + serviços de orquestração
  domain/                   # Regras, presenter, policies, ports
  infrastructure/           # Postgres, LLM, gateways
  content/pt-BR/            # Textos PT-BR (JSON)
migrations/                 # Alembic
docs/                       # Documentação técnica (ver docs/README.md)
tests/unit/                 # pytest
scripts/                    # Smokes, sync OpenAPI
```

Detalhes: [docs/development/guia-desenvolvimento.md](docs/development/guia-desenvolvimento.md).

## Funcionalidades principais

- Chat com histórico, streaming SSE (`playback`, `canvas_open`), lousa, anexos e artefatos
- RAG documental (pgvector); RAG híbrido, rerank e loop agentic (configurável)
- Respostas diretas (identidade, small talk, utilidades, operacional) sem LLM quando aplicável
- Diagnóstico **`adminDebug`** persistido em todo turno; visível na API/UI só para admin
- **Agentes** com rascunho/publicação, preview, skills, fontes e actions OpenAPI
- **Projetos** com instruções, agente padrão e contexto compartilhado
- Base global de conhecimento com pipeline de ingestão
- Painel admin: diretrizes, métricas, auditoria, simulação, avaliações
- Apresentação rica: tabelas, gráficos, árvore, KPI, multi-rota produto
- Pesquisa web, OCR/visão documental, SQL avançado, escrita de e-mail

## Testes

```bash
pytest tests/unit -q
```

Índice completo: [docs/testing/README.md](docs/testing/README.md).

Smoke local (identidade + RAG, dentro do container com DB):

```bash
docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
  python scripts/smoke_identity_rag.py <user_id> <session_id> "quem te criou?"
```

## Variáveis de ambiente

Seleção das principais — lista completa em `app/infrastructure/config/settings.py` e `infra/.env.dev.example`.

| Variável | Descrição |
|----------|-----------|
| `DATABASE_URL` | PostgreSQL + pgvector (obrigatória) |
| `LLM_PROVIDER` | `ollama` ou `vllm` |
| `OLLAMA_MODEL` | Default `qwen2.5:1.5b` |
| `RAG_CONTEXT_MIN_SCORE` | Score mínimo de chunk no contexto |
| `CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED` | Identidade sem LLM (default `true`) |
| `CHAT_PERSIST_BEFORE_PLAYBACK` | Persistência antes do playback (default `true`) |
| `CHAT_AGENTIC_LOOP_ENABLED` | Loop agentic (default `false`) |
| `CHAT_WEB_SEARCH_ENABLED` | Pesquisa web |
| `CHAT_DOCUMENT_VISION_ENABLED` | OCR PDF/imagem |

Perfis dev/prod: [docs/knowledge/chat-intelligence-settings-profiles.md](docs/knowledge/chat-intelligence-settings-profiles.md).
