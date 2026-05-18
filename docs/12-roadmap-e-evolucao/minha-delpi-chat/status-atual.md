# Status Atual — Minha DELPI Chat

> Atualizado após conclusão do roadmap admin (itens 1–15) e melhorias futuras (maio/2026).

## Visão geral

O Minha DELPI Chat é um microfrontend oficial da plataforma com backend dedicado `minha-delpi-ai-api`, autenticação Keycloak, autorização Core API/RBAC, PostgreSQL + pgvector, streaming SSE, RAG, tools, auditoria e painel administrativo completo.

## Documentação oficial

| Documento | Caminho |
|-----------|---------|
| API | [minha-delpi-ai-api/docs/api/README.md](../../../minha-delpi-ai-api/docs/api/README.md) |
| Backend README | [minha-delpi-ai-api/README.md](../../../minha-delpi-ai-api/README.md) |
| Plugin README | [plugins/minha-delpi-chat/README.md](../../../plugins/minha-delpi-chat/README.md) |
| Roadmap admin | [minha-delpi-ai-api/docs/roadmap/admin-minha-delpi-chat.md](../../../minha-delpi-ai-api/docs/roadmap/admin-minha-delpi-chat.md) |
| Melhorias futuras | [minha-delpi-ai-api/docs/roadmap/melhorias-futuras.md](../../../minha-delpi-ai-api/docs/roadmap/melhorias-futuras.md) |

## Estado funcional

### Chat (usuário final)

- Sessões, histórico, streaming, pin/arquivo, edição de mensagem
- RAG com fontes, tools, anexos, projetos e agentes
- **Feedback** thumbs up/down nas respostas do assistente
- Segurança de entrada (sanitização, anti-injection, modo enforce/monitor)

### Painel administrativo

| Área | Status |
|------|--------|
| Conhecimento global | Upload, metadados curadoriais, pipeline, pré-visualização texto/arquivo, dedup semântica |
| Diretrizes | CRUD, versões, ambientes, teste RAG |
| Métricas | Janela 24h/7d/30d, timeseries, custo LLM editável no banco |
| Simulação | Prompt/RAG/diretrizes/tools; histórico de sessão; sandbox de tools |
| Avaliações | Nota, veredito, sugestões regras + LLM opcional |
| Agentes | Especialização (escopo RAG, diretrizes, tools) |
| Segurança | Config, summary, eventos, scan |
| Ferramentas | Health consolidado, external actions, LLM |
| Auditoria | Paginação, filtros, timeline, export CSV, trace id |

### Roadmaps

- **Admin itens 1–15:** concluídos — ver `admin-minha-delpi-chat.md`
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

- Provider: **Ollama** (`qwen2.5:1.5b` + `bge-m3`)
- vLLM pendente de host com GPU — ver `homologacao-vllm-producao.md`

## Endpoints de verificação rápida

```text
GET  /apps/minha-delpi-ai/api/health
GET  /apps/minha-delpi-ai/api/admin/system-check
GET  /apps/minha-delpi-ai/api/admin/tools/health
GET  /apps/minha-delpi-ai/api/admin/metrics/summary?hours=24
GET  /apps/minha-delpi-ai/api/chat/capabilities
```

## Próximas evoluções sugeridas

1. RBAC formal no Core API (perfis centralizados)
2. Notificações — ver [notificacoes-minha-delpi.md](../../../minha-delpi-ai-api/docs/roadmap/notificacoes-minha-delpi.md)
3. Observabilidade Prometheus/Grafana
4. Homologação vLLM em GPU
5. Tools operacionais (`search_lmp`, etc.) com RBAC dedicado
