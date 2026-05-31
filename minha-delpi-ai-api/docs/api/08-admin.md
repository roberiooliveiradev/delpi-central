# 08 — Admin API

A maioria dos endpoints abaixo exige `minha-delpi.chat.admin`. Exceções indicadas (ex.: catálogo de **Skills** usa `minha-delpi.chat.tools.manage`).

## Skills — catálogo global

Gerencia entradas em `ai_chat_skill_catalog` (policies Markdown, flags, ordem). A aba **Skills** no painel admin do chat consome estas rotas.

| Método | Path | Permissão |
|---|---|---|
| GET | `/admin/skills` | `tools.manage` |
| POST | `/admin/skills` | `tools.manage` |
| PUT | `/admin/skills/{skillId}` | `tools.manage` |
| DELETE | `/admin/skills/{skillId}` | `tools.manage` (desativa: `is_active=false`) |

Detalhes de campos e vínculo por agente: [`11-skills.md`](11-skills.md).

---

## External action providers globais

### GET `/admin/external-action-providers`

Lista providers externos globais.

### POST `/admin/external-action-providers`

Cria provider externo global.

Body típico:

```json
{
  "providerKey": "api-delpi",
  "name": "API DELPI",
  "type": "openapi",
  "baseUrl": "https://...",
  "openApiUrl": "https://.../openapi.json",
  "authMode": "user_token",
  "authConfig": {},
  "enabled": true
}
```

### POST `/admin/external-action-providers/{providerKey}/schema`

Importa schema OpenAPI enviado no body.

### POST `/admin/external-action-providers/{providerKey}/reload-schema`

Recarrega schema usando `openApiUrl` salvo no provider.

### GET `/admin/external-actions`

Lista actions externas globais.

Query params:

| Parâmetro | Descrição |
|---|---|
| `provider` | Filtra por provider key. |

---

## Saúde operacional

### GET `/admin/system-check`

Executa checks administrativos do sistema (banco, pgvector, tabelas obrigatórias, LLM).

### GET `/admin/tools/health`

Health consolidado para a aba **Ferramentas** do admin.

Inclui status de banco, pgvector, schema, LLM, Core API (`/me` com token do admin), catálogo de external actions e providers.

Resposta:

```json
{
  "status": "ok",
  "systemCheck": { },
  "items": [
    {
      "id": "database",
      "label": "Banco de dados",
      "status": "ok",
      "description": "..."
    }
  ]
}
```

### GET `/admin/metrics/summary`

Resumo de métricas administrativas.

Query:

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `hours` | `24` | Janela analisada (máx. `ADMIN_METRICS_MAX_HOURS`, default 720). |

Resposta inclui `windowHours`. O bloco `advanced` inclui:

| Campo | Descrição |
|---|---|
| `latencyAvgMs` | Latência média das mensagens instrumentadas (24h). |
| `tokensUsed` | Tokens estimados (24h). |
| `estimatedCost` | Custo estimado total (24h). |
| `ragFailures` | Mensagens com RAG sem fontes. |
| `assertivenessRate` | Taxa de testes RAG assertivos (24h). |
| `ragTests24h` | Total de testes RAG registrados. |
| `agentMetrics` | Distribuição por `agentKey`. |
| `userProfileMetrics` | Distribuição por `userId`. |
| `costTable` | Tabela configurada de custo por provider/modelo. |
| `costBreakdown24h` | Uso e custo agregados por provider/modelo. |

Custo: prioridade para tabela persistida em `ai_admin_runtime_settings` (`llm_cost_table`); fallback `LLM_COST_TABLE_JSON`.

### GET `/admin/metrics/timeseries`

Série temporal agregada por buckets.

Query:

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `hours` | `168` | Janela total |
| `bucketHours` | `24` | Tamanho de cada bucket |

Resposta: `windowHours`, `bucketHours`, `buckets[]` com `auditLogs`, `tokensUsed`, `estimatedCost`, `latencyAvgMs` por intervalo.

### GET `/admin/metrics/cost-table`

Retorna tabela de custo por provider/modelo.

```json
{
  "entries": [
    {
      "provider": "ollama",
      "model": "qwen2.5:1.5b",
      "promptCostPer1k": 0,
      "completionCostPer1k": 0,
      "currency": "BRL",
      "source": "database"
    }
  ],
  "source": "database"
}
```

### PUT `/admin/metrics/cost-table`

Persiste a tabela no banco (substitui env até novo deploy).

Body:

```json
{
  "entries": [
    {
      "provider": "ollama",
      "model": "qwen2.5:1.5b",
      "promptCostPer1k": 0.001,
      "completionCostPer1k": 0.002,
      "currency": "BRL"
    }
  ]
}
```

Auditoria: `admin.metrics.cost_table.updated`.

Variáveis de ambiente: `LLM_COST_TABLE_JSON`, `RAG_ASSERTIVENESS_MIN_SCORE`, `ADMIN_METRICS_MAX_HOURS`.

### GET `/admin/llm/status`

Status do provider LLM configurado.

### GET `/admin/rbac/summary`

Resumo de perfis, permissões e capabilities administrativas. Inclui `formalProfiles`, `activeFormalProfiles` e `formalProfileMatrix` (bridge 11.6).

### GET `/admin/rbac/profiles`

Catálogo formal de perfis RBAC do chat (`admin`, `operator`, `auditor`, `viewer`) e contrato de integração com o core-api.

---

## Administração da base de conhecimento

### GET `/admin/knowledge/documents`

Lista documentos de knowledge com paginação.

Query params:

| Parâmetro | Default | Descrição |
|---|---:|---|
| `limit` | `20` | Quantidade máxima. |
| `offset` | `0` | Paginação. |
| `search` | — | Filtro textual (título, tipo, referência e metadados curadoriais). |
| `active` | — | Filtro por ativo/inativo. |
| `category` | — | Categoria curatorial. |
| `namespace` | — | Namespace curatorial. |
| `domain` | — | Domínio curatorial. |
| `tag` | — | Tag (match parcial em `metadata.tags`). |
| `sourceType` | — | Tipo de fonte do documento. |

Resposta inclui `facets` (categorias, namespaces, domínios, tags e tipos de fonte disponíveis na base global), `summary` (contagens globais: `total`, `active`, `inactive`, `pendingIndex` — ativos sem chunks) e campos curadoriais em cada item (`category`, `tags`, `namespace`, `domain`, `priority`, `qualityScore`).

### PATCH `/admin/knowledge/documents/{documentId}/metadata`

Atualiza metadados curadoriais de um documento global.

Body (todos opcionais):

```json
{
  "category": "atendimento",
  "tags": ["faq", "onboarding"],
  "namespace": "global:rh",
  "domain": "recursos-humanos",
  "priority": 3,
  "qualityScore": 85
}
```

### POST `/admin/knowledge/ingest/preview`

Simula o pipeline de ingestão (limpeza, chunk adaptativo, deduplicação exata e **deduplicação semântica**) sem persistir documento/chunks.

**JSON** (`Content-Type: application/json`):

```json
{
  "content": "texto bruto",
  "title": "opcional",
  "sourceType": "manual",
  "sourceRef": "global:exemplo",
  "metadata": { "scope": "global" },
  "checkSemanticDuplicates": true
}
```

**Multipart** (`file` + campos de formulário): extrai texto do arquivo (mesmos formatos do upload) e executa o mesmo pipeline.

Campos multipart: `file`, `title`, `sourceType`, `sourceRef`, `checkSemanticDuplicates` (`false` para desligar).

Resposta: `cleanedPreview`, `chunks[]`, `pipeline`, e opcionalmente `semanticDuplicates[]` (`documentId`, `chunkId`, `similarity`, `preview`).

Env: `KNOWLEDGE_SEMANTIC_DEDUP_ENABLED`, `KNOWLEDGE_SEMANTIC_DEDUP_THRESHOLD` (default `0.92`).

### POST `/admin/knowledge/documents/upload`

Upload de arquivo com campos curadoriais opcionais no `multipart/form-data`: `category`, `tags`, `namespace`, `domain`, `priority`, `qualityScore` (além de `metadata` JSON legado).

Respostas de ingestão/reindex incluem `pipeline` com estatísticas. Quando `sourceRef` + `contentHash` já existem na base global, a API retorna `duplicate: true` e `skipped: true` sem criar chunks novos.

### POST `/admin/knowledge/documents/{documentId}/deactivate`

Desativa documento.

### POST `/admin/knowledge/documents/{documentId}/reactivate`

Reativa documento.

### POST `/admin/knowledge/documents/{documentId}/reindex`

Reindexa documento.

---

## Avaliação de respostas

### GET `/admin/responses/evaluations/summary`

Resumo agregado: total, média de nota, taxa de respostas úteis, distribuição por `verdict`, avaliações nas últimas 24h.

### GET `/admin/responses/candidates`

Lista respostas recentes do assistente (`role=assistant`) para avaliação, com avaliação existente quando houver.

Query: `search`, `limit`, `offset`.

### GET `/admin/responses/messages/{messageId}/evaluation-context`

Retorna pergunta do usuário, resposta, metadados RAG/diretrizes/tools e **sugestões automáticas** para o score informado.

Query:

| Parâmetro | Descrição |
|-----------|-----------|
| `score` | 1-5 (opcional; default da avaliação existente ou 3) |
| `useLlmSuggestions` | `true` para enriquecer sugestões com LLM (mais lento) |

Env: `RESPONSE_EVALUATION_LLM_SUGGESTIONS_ENABLED`.

### GET `/admin/responses/evaluations`

Lista avaliações salvas com filtros (`verdict`, `minScore`, `maxScore`, `search`).

### POST `/admin/responses/evaluations`

Salva ou atualiza avaliação de uma mensagem.

Body:

```json
{
  "messageId": "uuid-da-mensagem-assistente",
  "score": 4,
  "comment": "Resposta correta, mas faltou citar a política interna."
}
```

Gera `verdict` (`helpful` | `neutral` | `unhelpful`) e persiste sugestões para documentos/diretrizes. Auditoria: `admin.response.evaluated`.

---

## Agentes especializados

### GET `/admin/agents/specializations/catalog`

Lista presets de domínio (RH, TI, Financeiro, etc.).

### GET `/admin/agents/specialized`

Lista agentes habilitados com resumo de especialização.

### GET `/admin/agents/{agentId}/specialization`

Retorna configuração atual do agente.

### PUT `/admin/agents/{agentId}/specialization`

Salva especialização no `metadata` do agente.

Body:

```json
{
  "specialization": {
    "enabled": true,
    "presetKey": "rh",
    "domain": "recursos-humanos",
    "knowledgeDomains": ["recursos-humanos"],
    "knowledgeNamespaces": ["global:rh"],
    "knowledgeCategories": ["rh"],
    "knowledgeTags": ["rh", "ferias"],
    "guidelineCategories": ["rh", "behavior"],
    "allowedTools": ["get_current_user", "search_knowledge_base"],
    "includeGlobalKnowledge": true
  }
}
```

Quando ativo, o chat e a simulação passam a respeitar o escopo de RAG, diretrizes e tools do agente.

---

## Segurança operacional

### GET `/admin/security/config`

Retorna limites e limiares ativos (env).

### GET `/admin/security/summary?hours=24`

Resumo de bloqueios, sinalizações e scans nas últimas N horas.

### GET `/admin/security/events`

Lista eventos de segurança (`security.input.*`, `admin.security.scanned`).

### POST `/admin/security/scan`

Analisa uma mensagem sem enviar ao chat.

Body:

```json
{ "message": "texto para testar" }
```

Resposta inclui `analysis.riskScore`, `flags`, `wouldBlock` e `wouldFlag`.

No chat, mensagens bloqueadas retornam `422` com código `security.input_blocked`.

---

## Diretrizes administrativas

Ver rotas em `admin_routes.py`: listagem, salvamento, publicação, arquivamento, versões, comparação, restauração e `/admin/rag/test`.

---

## Simulação completa do agente

### POST `/admin/agent/simulate`

Simula o comportamento do agente sem persistir sessão/mensagem.

Body:

```json
{
  "question": "Como responder sobre férias?",
  "agentId": "uuid-opcional",
  "agentKey": "opcional",
  "documentId": "opcional",
  "sessionId": "uuid-opcional",
  "generateAnswer": false,
  "executeToolsInSandbox": false
}
```

| Campo | Descrição |
|-------|-----------|
| `sessionId` | Carrega até `CHAT_HISTORY_MAX_MESSAGES` mensagens reais da sessão do admin no histórico do prompt |
| `executeToolsInSandbox` | Se `true`, executa tools via `ChatToolContextService` com token do admin; senão apenas lista tools **planejadas** |
| `generateAnswer` | Se `true`, chama LLM para `answerPreview` |

Resposta inclui:

- `finalPrompt`, `appliedGuidelines`, `chunks`, `matchedDocuments`
- `plannedToolCalls` — planejadas ou executadas (sandbox)
- `sessionHistory` — resumo do histórico injetado
- `comparison` — com/sem diretrizes e com/sem RAG
- `answerPreview`
- `debugContext` — inclui `historyMessageCount`, `executeToolsInSandbox`

Registra auditoria `admin.agent.simulated`.

---

## Auditoria

### GET `/admin/audit-logs`

Lista logs administrativos com paginação e filtros.

Query params:

| Parâmetro | Default | Descrição |
|---|---:|---|
| `limit` | `50` | Máximo 200 por página. |
| `offset` | `0` | Deslocamento. |
| `action` | — | Filtro parcial por ação. |
| `context` | — | Filtro parcial por contexto. |
| `userId` | — | UUID do usuário. |
| `traceId` | — | ID de correlação da requisição (`X-Trace-ID` / `X-Request-ID`). |
| `search` | — | Busca em ação, contexto, usuário, hash e trace. |
| `dateFrom` | — | ISO date ou datetime (início). |
| `dateTo` | — | ISO date ou datetime (fim). |

Resposta:

```json
{
  "items": [],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 0,
    "hasNext": false,
    "hasPrevious": false
  },
  "filters": {}
}
```

### GET `/admin/audit-logs/timeline`

Agrupa eventos por dia com totais, distribuição por ação e amostra recente.

Query params: mesmos filtros de listagem + `maxDays` (default 31, máx. 90).

### GET `/admin/audit-logs/export`

Exporta até 5000 registros com os mesmos filtros (sem paginação). Requer `minha-delpi.chat.admin`.

- `format=json` (padrão): resposta JSON.
- `format=csv`: download `text/csv` com colunas `id`, `createdAt`, `traceId`, `action`, etc.

### GET `/admin/audit-logs/{logId}`

Detalhe do evento, correlacionados por `promptHash` e por `traceId`.

Resposta:

```json
{
  "log": {},
  "relatedLogs": [],
  "traceRelatedLogs": []
}
```

Cada novo evento de auditoria recebe `traceId` da requisição HTTP (`X-Trace-ID`, `X-Request-ID` ou UUID gerado).

---

## Smoke automatizado (homologação)

Login Keycloak (`rober` / `1234` em dev) + rotas admin críticas:

```bash
cd minha-delpi-ai-api
SMOKE_BASE_URL=http://localhost python scripts/smoke_admin_endpoints.py
```

Verifica: `GET /admin/knowledge/documents` (campo `summary`), `guidelines`, `metrics/summary`, `agents/specialized`, `responses/evaluations/summary`, `security/summary`, `rbac/summary` e `POST /admin/agent/simulate`.
