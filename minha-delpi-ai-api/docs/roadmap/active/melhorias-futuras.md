# Melhorias futuras — Minha DELPI Chat

Consolidado a partir da revisão de código (backend + plugin `minha-delpi-chat`) em maio/2026.

---

## Status geral

Todas as evoluções planejadas neste documento foram **implementadas**, exceto RBAC com perfis formais no core (escopo `core-api`, fora deste repositório).

| # | Tema | Status |
|---|------|--------|
| 1 | Feedback do usuário no chat (thumbs up/down) | Concluído |
| 2 | `GET /admin/tools/health` | Concluído |
| 3 | UI para editar tabela de custo LLM | Concluído |
| 4 | Métricas com histórico > 24h | Concluído |
| 5 | Simulação com histórico real de sessão | Concluído |
| 6 | Sandbox de execução de tools na simulação | Concluído |
| 7 | Pré-visualização de ingestão para upload de arquivo | Concluído |
| 8 | Deduplicação semântica (embeddings) | Concluído |
| 9 | Sugestões de avaliação via LLM | Concluído |
| 10 | RBAC com perfis formais no core | Pendente (core-api) |

---

## Entregas desta onda

### 1 — Feedback no chat

- Tabela `ai_chat_message_feedback` (rating `-1` / `1` por mensagem e usuário)
- `PUT /chat/sessions/{sessionId}/messages/{messageId}/feedback`
- Histórico retorna `user_feedback` nas mensagens do assistente
- UI: thumbs up/down em `ChatMessageList`

### 2 — Health de ferramentas

- `GET /admin/tools/health` — consolida system-check, core-api, catálogo de actions e providers
- Frontend `getAdminToolHealth` passa a consumir o endpoint real

### 3 — Tabela de custo LLM editável

- Tabela `ai_admin_runtime_settings` (chave `llm_cost_table`)
- `GET/PUT /admin/metrics/cost-table`
- `LlmCostEstimatorService` prioriza valor persistido no banco
- Painel de métricas com edição e salvamento

### 4 — Métricas históricas

- `GET /admin/metrics/summary?hours=24|168|720`
- `GET /admin/metrics/timeseries?hours=&bucketHours=`
- Seletor de janela (24h / 7d / 30d) no admin

### 5 e 6 — Simulação avançada

- `sessionId` opcional carrega histórico real da sessão no prompt
- `executeToolsInSandbox` executa tools via `ChatToolContextService` (com token do admin)
- UI: seleção de sessão e checkbox de sandbox

### 7 — Pré-visualização de arquivo

- `POST /admin/knowledge/ingest/preview` aceita `multipart/form-data` com `file`
- Painel de ingestão permite pré-visualizar também no modo arquivo

### 8 — Deduplicação semântica

- `KnowledgeSemanticDeduplicatorService` (similaridade por embedding + pgvector)
- Pré-visualização retorna `semanticDuplicates`
- Env: `KNOWLEDGE_SEMANTIC_DEDUP_ENABLED`, `KNOWLEDGE_SEMANTIC_DEDUP_THRESHOLD`

### 9 — Sugestões via LLM nas avaliações

- `ResponseEvaluationLlmSuggestionService`
- `GET .../evaluation-context?useLlmSuggestions=true`
- Checkbox no painel de avaliações
- Env: `RESPONSE_EVALUATION_LLM_SUGGESTIONS_ENABLED`

---

## Migrations

Rodar após deploy:

```bash
flask --app app.main:app db upgrade
```

Novas revisões:

- `d5e6f7a8b9c0` — `ai_chat_message_feedback`
- `e6f7a8b9c0d1` — `ai_admin_runtime_settings`

---

## Pendência externa

**RBAC com perfis formais no core:** continua dependendo de evolução no `core-api` (perfis/roles centralizados). O chat admin expõe `GET /admin/rbac/summary` (capacidades derivadas) e **`GET /admin/rbac/profiles`** (catálogo formal bridge 11.6).
