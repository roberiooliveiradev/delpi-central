# Melhorias futuras — Minha DELPI Chat

Consolidado a partir da revisão de código (backend + plugin `minha-delpi-chat`) em maio/2026.

---

## Débitos corrigidos nesta onda

| Item | Problema | Correção |
|---|---|---|
| Métricas — falhas RAG | `postgres_admin_metrics_repository` lia `row.metadata` (inexistente no model) | Usar `row.audit_metadata` |
| Roadmap consolidado | Seção “Pendente” desatualizada | Atualizado em `admin-minha-delpi-chat.md` |
| Auditoria admin | Frontend com filtros/tabela sem backend | Item 9 entregue (paginação, filtros, exportação, detalhe) |

---

## Item 8 — Métricas avançadas (concluído no escopo atual)

### Entregue

- Tabela de custo (`LLM_COST_TABLE_JSON`, `advanced.costTable`)
- Breakdown de custo 24h (`advanced.costBreakdown24h`)
- Assertividade RAG (`admin.rag.tested`, `RAG_ASSERTIVENESS_MIN_SCORE`)
- Métricas por usuário (`advanced.userProfileMetrics`)

### Evolução futura

- UI para editar tabela de custo sem redeploy
- Séries históricas (>24h)

---

## Item 9 — Auditoria avançada (concluído no escopo atual)

### Entregue

- Paginação e filtros em `/admin/audit-logs`
- Exportação em `/admin/audit-logs/export`
- Detalhe e correlação em `/admin/audit-logs/{id}`
- Painel admin integrado com RBAC de exportação

### Evoluções posteriores (concluídas)

- Timeline agrupada por dia (`GET /admin/audit-logs/timeline`)
- Exportação CSV (`GET /admin/audit-logs/export?format=csv`)
- Trace id dedicado (`trace_id` + filtro `traceId` + correlação no detalhe)

---

## Item 6 — Ferramentas (lacuna residual)

- `getAdminToolHealth` no frontend ainda usa stub local quando não há endpoint dedicado de health por tool
- Evolução: `GET /admin/tools/health` consolidado ou reutilizar `/admin/system-check`

---

## Itens 10–15 — Backlog

| # | Tema | Resumo |
|---|---|---|
| 10 | Simulação do agente | Pergunta de teste com prompt final, tool calls e comparação com/sem diretrizes/RAG |
| 11 | Conhecimento avançado | Tags, categorias, prioridade, namespaces, filtros |
| 12 | Pipeline de ingestão | Chunk adaptativo, deduplicação, limpeza, metadados enriquecidos |
| 13 | Avaliação de respostas | Feedback, score, sugestões de diretriz/documento |
| 14 | Agentes especializados | Concluído — presets, escopo RAG, diretrizes e tools por agente |
| 15 | Segurança operacional | Concluído — sanitização, anti-injection, limites, auditoria e aba admin |

---

## Item 10 — Simulação completa do agente (concluído)

### Entregue

- `POST /admin/agent/simulate`
- Aba Simulação no admin
- Prompt final, diretrizes, chunks, tools previstas, comparações
- Opção de resposta via LLM

### Evolução futura

- Histórico real de sessão na simulação
- Sandbox de execução de tools

---

## Item 12 — Pipeline de ingestão (concluído)

### Entregue

- `KnowledgeIngestionPipelineService` (limpeza, chunk adaptativo, deduplicação)
- Metadados `contentHash` / `ingestionPipeline` em documentos e chunks
- `POST /admin/knowledge/ingest/preview`
- Pré-visualização no painel admin (modo texto)
- Skip de duplicata por `sourceRef` + `contentHash`

### Evolução futura

- Pré-visualização também para upload de arquivo (extração local)
- Deduplicação semântica (embeddings) além de hash exato

---

## Item 13 — Avaliação de respostas (concluído)

### Entregue

- Persistência de avaliações com nota, veredito e sugestões
- API admin de candidatos, contexto e resumo
- Aba Avaliações no painel

### Evolução futura

- Feedback do usuário final no chat (thumbs up/down)
- Sugestões via LLM com base no histórico de avaliações

---

## Próxima ação recomendada

1. Feedback do usuário final no chat (thumbs)
2. Health dedicado por tool (`GET /admin/tools/health`)
3. UI para editar tabela de custo LLM no painel
