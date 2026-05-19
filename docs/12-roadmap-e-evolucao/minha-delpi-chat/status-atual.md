# Status Atual — Minha DELPI Chat

> Atualizado após conclusão da **Onda 6** de inteligência do chat, roadmap admin (itens 1–15) e melhorias futuras (maio/2026).

## Visão geral

O Minha DELPI Chat é um microfrontend oficial da plataforma com backend dedicado `minha-delpi-ai-api`, autenticação Keycloak, autorização Core API/RBAC, PostgreSQL + pgvector, streaming SSE, RAG, tools, auditoria e painel administrativo completo.

## Documentação oficial

| Documento | Caminho |
|-----------|---------|
| API | [minha-delpi-ai-api/docs/api/README.md](../../../minha-delpi-ai-api/docs/api/README.md) |
| Backend README | [minha-delpi-ai-api/README.md](../../../minha-delpi-ai-api/README.md) |
| Plugin README | [plugins/minha-delpi-chat/README.md](../../../plugins/minha-delpi-chat/README.md) |
| Roadmap admin | [minha-delpi-ai-api/docs/roadmap/admin-minha-delpi-chat.md](../../../minha-delpi-ai-api/docs/roadmap/admin-minha-delpi-chat.md) |
| Gestão de agentes | [minha-delpi-ai-api/docs/roadmap/agentes-gestao-melhorias.md](../../../minha-delpi-ai-api/docs/roadmap/agentes-gestao-melhorias.md) |
| Inteligência do chat | [minha-delpi-ai-api/docs/roadmap/README.md](../../../minha-delpi-ai-api/docs/roadmap/README.md) |
| Onda 6 (inteligência) | [inteligencia-chat-onda-6.md](../../../minha-delpi-ai-api/docs/roadmap/inteligencia-chat-onda-6.md) |
| Onda 7 (inteligência) | [inteligencia-chat-onda-7.md](../../../minha-delpi-ai-api/docs/roadmap/inteligencia-chat-onda-7.md) |
| Guia api-delpi para agentes | [api-delpi-rotas-agente.md](../../../minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md) |
| Melhorias futuras | [minha-delpi-ai-api/docs/roadmap/melhorias-futuras.md](../../../minha-delpi-ai-api/docs/roadmap/melhorias-futuras.md) |

## Estado funcional

### Chat (usuário final)

- Sessões, histórico, streaming, pin/arquivo, edição de mensagem
- RAG com fontes, tools, anexos, projetos e agentes
- **Gestão de agentes** (builder, shares, stats, duplicate, export/import, transfer) — ondas 1–7
- **Feedback** thumbs up/down nas respostas do assistente
- Segurança de entrada (sanitização, anti-injection, modo enforce/monitor)
- Inteligência configurável: RAG híbrido, rerank, loop agentic, cache de embeddings (admin)
- **Pipeline operacional (Onda 6):** fast path, seleção heurística de actions OpenAPI, resposta direta (produto/LMP/SQL), metadados `intelligence` (timings, action, pipeline)
- Timeline de mensagens (estilo mensageiro), pin no topo durante stream, primeira pergunta visível ao enviar

### Painel administrativo

| Área | Status |
|------|--------|
| Conhecimento global | Upload, metadados curadoriais, pipeline, pré-visualização texto/arquivo, dedup semântica |
| Diretrizes | CRUD, versões, ambientes, teste RAG |
| Métricas | Janela 24h/7d/30d, timeseries, custo LLM editável no banco |
| Simulação | Prompt/RAG/diretrizes/tools; histórico de sessão; sandbox de tools |
| Avaliações | Nota, veredito, sugestões regras + LLM opcional |
| Agentes | Especialização (escopo RAG, diretrizes, tools) + painel de estatísticas de uso |
| Segurança | Config, summary, eventos, scan |
| Ferramentas | Health consolidado, external actions, LLM |
| Auditoria | Paginação, filtros, timeline, export CSV, trace id |

### Roadmaps

- **Admin itens 1–15:** concluídos — ver `admin-minha-delpi-chat.md`
- **Gestão de agentes ondas 1–7:** concluídas — ver `agentes-gestao-melhorias.md`
- **Inteligência do chat ondas 1–6:** concluídas — ver `roadmap/README.md` e `inteligencia-chat-onda-6.md` em `minha-delpi-ai-api`
- **Inteligência Onda 7:** em andamento — templates de instruções no builder (7.1 concluído)
- **Melhorias futuras:** concluídas neste repositório — ver `melhorias-futuras.md`
- **Pendente externo:** RBAC com perfis formais no `core-api`

## Banco de dados

- Serviço: `postgres-plugins` (`pgvector/pgvector:pg15`)
- Porta host dev: `5433`
- Migrations: `flask --app app.main:app db upgrade`

Tabelas principais (não exaustivo):

```text
ai_chat_sessions, ai_chat_messages, ai_chat_message_feedback
ai_knowledge_documents, ai_knowledge_chunks
ai_audit_logs, ai_admin_runtime_settings, ai_response_evaluations
ai_external_action_*, ai_chat_agent_*, ai_admin_guideline*
```

## Deploy e migrations

```bash
cd infra
docker compose -f docker-compose.dev.yml --env-file .env exec minha-delpi-ai-api \
  sh -lc "cd /app && flask --app app.main:app db upgrade"
```

Local (WSL) com `DATABASE_URL` apontando para `localhost:5433` — ver [09-deploy-migrations-schema.md](../../../minha-delpi-ai-api/docs/api/09-deploy-migrations-schema.md).

## LLM em produção (provisório)

- Provider: **Ollama** (`qwen2.5:1.5b` chat + `bge-m3` embeddings; CPU sem GPU). Qualidade vem do pipeline (actions, RAG, fast paths), não de modelo maior
- vLLM pendente de host com GPU — ver `homologacao-vllm-producao.md`

## Endpoints de verificação rápida

```text
GET  /apps/minha-delpi-ai/api/health
GET  /apps/minha-delpi-ai/api/admin/system-check
GET  /apps/minha-delpi-ai/api/admin/tools/health
GET  /apps/minha-delpi-ai/api/admin/metrics/summary?hours=24
GET  /apps/minha-delpi-ai/api/chat/capabilities
```

## Inteligência do chat (Onda 6) — concluída

Roadmap: [`inteligencia-chat-onda-6.md`](../../../minha-delpi-ai-api/docs/roadmap/inteligencia-chat-onda-6.md).

| Entrega | Status |
|---------|--------|
| Modelo padrão `qwen2.5:1.5b` + env CPU | Concluído |
| Fast path operacional | Concluído |
| Seleção de actions (produto, estoque, LMP, SQL, suprimentos) | Concluído |
| Resposta direta sem LLM (produto, LMP, SQL, genérico) | Concluído |
| Prompts `operational-agent.md` + `api-delpi-routes.md` | Concluído |
| OpenAPI api-delpi enriquecido (`operationId`, summaries PT) | Concluído |
| Doc RAG para agentes (`docs/knowledge/api-delpi-rotas-agente.md`) | Concluído |
| Metadados `intelligence` (timings, `selectedExternalAction`, `pipeline`) | Concluído |
| Fixtures de regressão (`tests/fixtures/chat_intelligence_regression_cases.py`) | Concluído |

**Produção recomendada (CPU):** `CHAT_OPERATIONAL_FAST_PATH_ENABLED=true`, `CHAT_EXTERNAL_ACTION_DIRECT_RESPONSE_ENABLED=true`, `EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED=false`, `CHAT_RAG_HYBRID_ENABLED=false`, `CHAT_RAG_PREFER_KEYWORD_SEARCH=true` — ver [variaveis-de-ambiente.md](../../02-infraestrutura/variaveis-de-ambiente.md).

**Após deploy da api-delpi:** reimportar OpenAPI no provider do agente e reindexar o documento de rotas na base de conhecimento.

**Homologação pendente:** latência &lt; 15s em CPU para pergunta operacional típica (estoque por código).

## api-delpi e agentes

- Metadados OpenAPI centralizados em `api-delpi/app/interface/http/openapi_agent_metadata.py`
- Guia técnico: [`api-delpi/docs/api/11-guia-agente-chat.md`](../../../api-delpi/docs/api/11-guia-agente-chat.md)

## Próximas evoluções sugeridas

1. RBAC formal no Core API (perfis centralizados)
2. Notificações — ver [notificacoes-minha-delpi.md](../../../minha-delpi-ai-api/docs/roadmap/notificacoes-minha-delpi.md)
3. Observabilidade Prometheus/Grafana
4. Homologação vLLM em GPU (latência com modelo maior)
5. Validação de latência Onda 6 em ambiente de produção real
6. ~~Templates de system prompt no builder~~ — concluído (Onda 7.1)
7. Expandir OpenAPI (compras, vendas, CPV/OTD) + regressão (Onda 7.2–7.3)
