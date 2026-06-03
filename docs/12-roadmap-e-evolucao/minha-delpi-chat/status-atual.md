# Status Atual — Minha DELPI Chat

> Atualizado em **maio/2026** — Onda 10, lousa por intent no chat base, persistência antes do playback e cadência de respostas prontas.

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
| Calibração RAG | [rag-context-min-score-calibracao.md](../../../minha-delpi-ai-api/docs/roadmap/rag-context-min-score-calibracao.md) |
| Guia api-delpi para agentes | [api-delpi-rotas-agente.md](../../../minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md) |
| Melhorias futuras | [minha-delpi-ai-api/docs/roadmap/melhorias-futuras.md](../../../minha-delpi-ai-api/docs/roadmap/melhorias-futuras.md) |

## Estado funcional

### Chat (usuário final)

- Sessões, histórico, streaming SSE (`assistant_pending`, `playback`, `canvas_open`), pin/arquivo, edição de mensagem
- **Lousa (canvas):** painel lateral editável; pedidos como «coloque na lousa/canvas/canva» reutilizam a última resposta do assistente (não confunde com Canva.com)
- **Playback:** resposta persistida no banco antes da animação de escrita (`CHAT_PERSIST_BEFORE_PLAYBACK`, default `true`)
- RAG com fontes, tools, anexos, projetos e agentes
- **Gestão de agentes** (builder, publicar/versões, preview rascunho, shares, stats, duplicate, export/import, transfer) — ondas 1–7 + publicação
- **Skills** injetadas automaticamente no chat comum (sem atalhos na home); por agente no builder
- **Feedback** thumbs up/down nas respostas do assistente
- Segurança de entrada (sanitização, anti-injection, modo enforce/monitor)
- Inteligência configurável: RAG híbrido, rerank, loop agentic, cache de embeddings (admin)
- **Pipeline operacional (Ondas 6–7):** fast path (slim prompt), warm-up Ollama, seleção heurística de actions OpenAPI (produto/search/OVs/giro/LMP/SQL), resposta direta sem LLM (produto/search/OVs/LMP/SQL), metadados `intelligence` (timings, action, pipeline)
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
- **Inteligência do chat ondas 1–10:** concluídas — ver `roadmap/README.md` e ondas 6–10 em `minha-delpi-ai-api`
- **Inteligência Onda 7:** concluída — templates (7.1), OpenAPI CPV/OTD/vendas (7.2), regressão (7.3), calibração RAG (7.4), homologação latência em prod (7.5), seleção OVs vs LMP (7.6), busca por descrição + roteamento (7.7), fix associação agent_key via context bar (7.8)
- **Inteligência Onda 8:** concluída — modelo 3b, features ativadas, apresentação inteligente, formato sob demanda
- **Inteligência Onda 9:** concluída — colunas preferenciais por tipo de dado, build com shared/delpi_auth, modal expandir, copiar API, streaming direct response, estabilidade memória (ctx 2048)
- **Inteligência Onda 10:** concluída — rotas `/products/{code}` e `/summary`, vocabulário e scoring de intent, fix OVs vs produto, títulos contextuais no presenter, doc RAG `api-delpi-rotas-agente.md` revisado
- **Melhorias futuras:** concluídas neste repositório — ver `melhorias-futuras.md`
- **Pendente externo:** RBAC com perfis formais no `core-api`

## Banco de dados

- Serviço: `postgres-plugins` (`pgvector/pgvector:pg15`)
- Porta host dev: `5433`
- Migrations: automáticas no boot (`docker-entrypoint.sh` → `flask db upgrade`)
- Contexto manual: `POST/DELETE .../memory/context-items` — texto, arquivo, **pergunta/resposta** (ações nas mensagens + diálogo «+»)

Tabelas principais (não exaustivo):

```text
ai_chat_sessions, ai_chat_messages, ai_chat_message_feedback
ai_knowledge_documents, ai_knowledge_chunks
ai_audit_logs, ai_admin_runtime_settings, ai_response_evaluations
ai_external_action_*, ai_chat_agent_*, ai_admin_guideline*
```

## Deploy e migrations

No Docker (dev/prod), `flask db upgrade` roda no entrypoint ao subir/reiniciar `minha-delpi-ai-api`. Ver logs: `docker compose logs minha-delpi-ai-api | head`.

Local (WSL) com `DATABASE_URL` apontando para `localhost:5433` — ver [09-deploy-migrations-schema.md](../../../minha-delpi-ai-api/docs/api/09-deploy-migrations-schema.md).

## LLM em produção

- Provider: **Ollama** (`qwen2.5:3b` chat + `bge-m3` embeddings; CPU sem GPU)
- Servidor: Intel Xeon Gold 5418Y (4 vCPUs), 7.8 GB RAM
- Configuração otimizada: `OLLAMA_NUM_THREAD=4`, `OLLAMA_MAX_LOADED_MODELS=2`, `OLLAMA_NUM_CTX=2048`, `LLM_MAX_TOKENS=1536`
- Modelo 3b (1.9 GB) + bge-m3 (1.1 GB) = ~3 GB — coexistem em 8 GB RAM com ctx=2048
- Temperature: 0.4 (respostas mais fluidas em português)
- Qualidade vem do modelo + pipeline (actions, RAG, fast paths, tool router, rerank)
- Streaming em respostas diretas: 4 chars/chunk, 20ms delay (efeito de escrita natural)
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

## Inteligência do chat (Onda 8) — concluída

| Entrega | Status |
|---------|--------|
| Modelo `qwen2.5:3b` (upgrade de 1.5b) | Concluído |
| Max tokens 1536 + ctx window 4096 | Concluído |
| Temperature 0.4 (respostas mais naturais) | Concluído |
| Tool Router ativado (seleção inteligente de ferramentas via LLM) | Concluído |
| RAG Hybrid ativado (vetorial + keyword combinados) | Concluído |
| RAG Rerank ativado (boost por relevância keyword) | Concluído |
| History Summary ativado (sumariza conversas longas) | Concluído |
| Semantic Rank ativado (ranking semântico de external actions) | Concluído |
| RAG: 8 chunks, 12000 chars (era 4/6000) | Concluído |
| Prompt base reformulado (pedir esclarecimento, manter contexto) | Concluído |
| Fast path restritivo (30 chars, mais knowledge hints) | Concluído |
| Apresentação inteligente: gráfico só quando faz sentido | Concluído |
| Formato sob demanda ("em tabela", "em gráfico", "só texto") | Concluído |
| Frontend toggle Gráfico/Tabela/Texto | Concluído |
| `availableFormats` no metadata de apresentação | Concluído |
| Flattening de objetos complexos em tabelas | Concluído |
| Todas as rotas de produto testadas e corrigidas | Concluído |

## Inteligência do chat (Onda 10) — concluída

Roadmap: [`inteligencia-chat-onda-10.md`](../../../minha-delpi-ai-api/docs/roadmap/inteligencia-chat-onda-10.md).

| Entrega | Status |
|---------|--------|
| Rotas `GET /products/{code}` e `/summary` na api-delpi | Concluído |
| Scoring de intent (descrição, parents, pricing, NF, OVs) | Concluído |
| Suite 36 cenários de seleção de rota (100%) | Concluído |
| Títulos contextuais no presenter por path | Concluído |
| Documentação RAG `api-delpi-rotas-agente.md` alinhada ao OpenAPI | Concluído |

## Inteligência do chat (Onda 9) — concluída

| Entrega | Status |
|---------|--------|
| Colunas preferenciais por tipo: fornecedores, clientes, roteiro, inspeção, movimentações, notas fiscais, preços | Concluído |
| `product_code` removido das tabelas quando redundante (foco em dados relevantes) | Concluído |
| Gráficos bloqueados em compras, vendas, movimentações, notas fiscais, preços | Concluído |
| `_is_tabular_data` expandido para guide, inspection, movements (tabela mesmo com 1 registro) | Concluído |
| Modal Expandir corrigido (registrado na modal-layer.css para portal) | Concluído |
| Botão "Copiar" na resposta bruta da API | Concluído |
| Dockerfile.prod: build context `.` + `shared/delpi_auth` | Concluído |
| Dependência `python-jose` adicionada (necessária para delpi_auth) | Concluído |
| Streaming em direct responses: 2 chars/chunk, 45ms delay (efeito de escrita) | Concluído |
| Intent «coloque na lousa» + SSE `canvas_open` (chat base, herda em agentes) | Concluído |
| Persistir resposta antes do playback (reload não perde texto em geração) | Concluído |
| Handoff stream → timeline sem piscar ao finalizar (`chatStreamHandoff`, maio/2026) | Concluído |
| Admin UX Playbook 11 (6 seções) | **Revertido** — 10 abas planas; mockups em `11_admin_ux_reorganizacao_abas/mockups/` |
| `OLLAMA_NUM_CTX=2048` — coexistência qwen2.5:3b + bge-m3 em 8GB RAM | Concluído |
| Perguntas ambíguas pedem esclarecimento (não encerram) | Concluído |
| Normalização de mensagens (typos/acentos) para seleção de actions | Concluído |
| Resposta direta "o que você pode fazer" (capacidades, APIs, actions) | Concluído |
| Capacidades no chat comum e em agentes (catálogo por agente) | Concluído |

**Produção recomendada (CPU com 8GB RAM):**
```env
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_NUM_CTX=2048
LLM_MAX_TOKENS=1536
LLM_TEMPERATURE=0.4
CHAT_TOOL_ROUTER_ENABLED=true
CHAT_RAG_HYBRID_ENABLED=true
CHAT_RAG_RERANK_ENABLED=true
CHAT_HISTORY_SUMMARY_ENABLED=true
EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED=true
CHAT_FAST_PATH_MAX_CHARS=30
MAX_CONTEXT_CHUNKS=8
MAX_CONTEXT_CHARS=12000
CHAT_OPERATIONAL_FAST_PATH_ENABLED=true
CHAT_EXTERNAL_ACTION_DIRECT_RESPONSE_ENABLED=true
CHAT_DIRECT_RESPONSE_STREAM_CHUNK_CHARS=2
CHAT_DIRECT_RESPONSE_STREAM_DELAY_MS=45
CHAT_PERSIST_BEFORE_PLAYBACK=true
```

**Após deploy da api-delpi:** reimportar OpenAPI no provider do agente e reindexar o documento de rotas na base de conhecimento.

**Homologação concluída:** latência 11s (greeting) e < 5s (consulta operacional direct response) em CPU prod — meta < 15s atingida.

## api-delpi e agentes

- Metadados OpenAPI centralizados em `api-delpi/app/interface/http/openapi_agent_metadata.py`
- Guia técnico: [`api-delpi/docs/api/11-guia-agente-chat.md`](../../../api-delpi/docs/api/11-guia-agente-chat.md)
- Documento RAG (ingestão): [`api-delpi-rotas-agente.md`](../../../minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md)
- Onda 10: [`inteligencia-chat-onda-10.md`](../../../minha-delpi-ai-api/docs/roadmap/inteligencia-chat-onda-10.md)

## Próximas evoluções sugeridas

1. RBAC formal no Core API (perfis centralizados)
2. Notificações — ver [notificacoes-minha-delpi.md](../../../minha-delpi-ai-api/docs/roadmap/notificacoes-minha-delpi.md)
3. Observabilidade Prometheus/Grafana
4. Homologação vLLM em GPU (latência com modelo maior)
5. ~~Templates de system prompt no builder~~ — concluído (Onda 7.1)
6. ~~OpenAPI CPV/OTD/vendas + regressão~~ — concluído (Onda 7.2–7.3)
7. ~~Calibração `RAG_CONTEXT_MIN_SCORE`~~ — guia publicado (Onda 7.4)
8. ~~Homologação latência < 15s em CPU prod~~ — concluído (Onda 7.5, 11s greeting)
9. ~~Warm-up Ollama no startup~~ — concluído (Onda 7, `ollama_warmup_service.py`)
10. ~~Redução de prompt para fast paths~~ — concluído (Onda 7, `CHAT_FAST_PATH_SLIM_PROMPT`)
11. ~~Modelo 3b + features de inteligência~~ — concluído (Onda 8)
12. ~~Apresentação flexível de dados~~ — concluído (Onda 8)
13. ~~Colunas preferenciais por rota~~ — concluído (Onda 9)
14. ~~Modal expandir + copiar API~~ — concluído (Onda 9)
15. ~~Streaming direct responses~~ — concluído (Onda 9)
16. ~~Estabilidade memória (ctx 2048)~~ — concluído (Onda 9)
17. Memória persistente entre sessões (preferências do usuário)
18. Cache de resultados de actions frequentes
19. Upgrade RAM servidor para modelo 7b + ctx 4096
20. Agentic loop multi-step habilitado em produção
