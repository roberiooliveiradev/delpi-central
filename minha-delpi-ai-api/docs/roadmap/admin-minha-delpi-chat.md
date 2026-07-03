# Roadmap — Administração Inteligente do Minha DELPI Chat

## Objetivo

Transformar o painel administrativo do Minha DELPI Chat em um centro operacional completo de governança da IA.

Documentos relacionados:

- [Melhorias futuras](./melhorias-futuras.md)
- [API Admin](../api/08-admin.md)

---

## Estado Atual

### Navegação admin (Playbook 11 — maio/2026)

- **6 seções** no topbar: Painel, Conhecimento, Agentes, Qualidade, Plataforma, Governança
- Sub-abas por seção; default `/admin` → **Painel**
- Deep links: `/admin/conhecimento/documentos`, `/admin/plataforma/inteligencia`, etc.
- Mobile: dropdown único (seção + sub-aba); sub-nav oculta em &lt;768px
- Status strip global: última atualização, erros e sucesso do `useChatAdmin`
- Cross-links: Segurança ↔ Auditoria; Especialização ↔ Builder (`/agentes`)

Detalhes: `plugins/minha-delpi-chat/src/ui/components/admin/README.md`.

### Já implementado

- Estrutura visual administrativa e abas modulares
- Base global de conhecimento (upload, exclusão, reindexação)
- Diretrizes (CRUD, versionamento, ambiente, prompt real)
- Teste RAG com explicabilidade
- Ferramentas reais (actions, providers, logs por agente)
- RBAC administrativo no painel
- Métricas operacionais e parte das métricas avançadas
- Auditoria inicial (listagem simples)

---

# Itens do roadmap

## 1. Aplicar diretrizes reais no prompt do chat

**Status: Concluído**

- Diretrizes ativas no system prompt (normal e streaming)
- Registro na auditoria (`admin_guideline_count`, `admin_guidelines`)

---

## 2. Versionamento de diretrizes

**Status: Concluído**

- Tabela `ai_admin_guideline_versions`
- Histórico, comparação e restauração como rascunho

---

## 3. Edição de diretrizes

**Status: Concluído**

- Editar, salvar rascunho, publicar e arquivar

---

## 4. Diretrizes por ambiente

**Status: Concluído**

- Ambientes: DEV, HOMOLOG, PROD (+ global)
- Filtro backend e aplicação conforme ambiente atual

---

## 5. Melhorar Teste RAG

**Status: Concluído**

- Diretrizes, documentos, chunks, score, `debugContext`, comparação com/sem diretrizes e RAG
- UI diferenciando tipos de fonte

---

## 6. Ferramentas reais

**Status: Concluído** (health dedicado por tool: evolução futura — ver [melhorias-futuras](./melhorias-futuras.md))

---

## 7. RBAC administrativo

**Status: Concluído no escopo atual**

- `/admin/rbac/summary`, matriz, bloqueios por aba
- Evolução: perfis formais no core; exportação já respeita `canExportAudit`

---

## 8. Métricas avançadas

**Status: Concluído no escopo atual**

### Entregue

- Distribuições e taxas 24h
- Latência, tokens, custo estimado
- Falhas RAG (`audit_metadata`)
- Mensagens por agente (`advanced.agentMetrics`)
- Eventos por usuário (`advanced.userProfileMetrics`)
- Tabela de custo por provider/modelo (`LLM_COST_TABLE_JSON` + `advanced.costTable`)
- Breakdown de custo 24h por provider/modelo (`advanced.costBreakdown24h`)
- Uso agregado por provider (`advanced.llmProviderUsage24h`) — Playbook 24 P5
- Snapshot rate limit API externa (`advanced.llmRateLimitSnapshot`) — Playbook 24 P5
- Assertividade RAG via auditoria de `/admin/rag/test` (`admin.rag.tested`)
- Limiar configurável: `RAG_ASSERTIVENESS_MIN_SCORE` (default `0.35`)

### Evolução futura

- Edição da tabela de custo via painel (hoje via env)
- Histórico de assertividade além de 24h

---

## 9. Auditoria avançada

**Status: Concluído no escopo atual**

### Entregue

- Paginação e filtros backend (`action`, `context`, `userId`, `search`, `dateFrom`, `dateTo`)
- Exportação JSON (`/admin/audit-logs/export`)
- Detalhe e correlação por `promptHash` (`/admin/audit-logs/{id}`)
- UI: filtros, resumo, tabela clicável, paginação, painel de detalhe
- RBAC de exportação (`canExportAudit`)

### Evolução futura

- Timeline agrupada, exportação CSV, trace id dedicado

---

## 10. Simulação completa do agente

**Status: Concluído no escopo atual**

### Entregue

- `POST /admin/agent/simulate`
- Prompt final (system) e preview seguro
- Diretrizes aplicadas, chunks e documentos
- Tools previstas (sem execução)
- Comparação com/sem diretrizes e com/sem RAG
- Opção `generateAnswer` para resposta via LLM
- Seleção opcional de agente
- Aba **Simulação** no painel admin
- Auditoria `admin.agent.simulated`

### Correção relacionada

- `AdminGuidelinePromptService` passou a usar `\n` real entre linhas (antes `\\n` literal)

### Evolução futura

- Simular com histórico de sessão real
- Executar tools em modo sandbox

---

## 11. Gestão avançada de conhecimento

**Status: Concluído no escopo atual**

### Entregue

- Metadados curadoriais: `category`, `tags`, `namespace`, `domain`, `priority`, `qualityScore`
- Filtros na listagem (`GET /admin/knowledge/documents`) + `facets` na resposta
- `PATCH /admin/knowledge/documents/{id}/metadata`
- Upload admin com campos curadoriais no multipart
- Painel admin: filtros, badges por `sourceType`, ingestão e edição inline de metadados
- Teste RAG por documento na lista

---

## 12. Pipeline inteligente de ingestão

**Status: Concluído no escopo atual**

### Entregue

- Limpeza de conteúdo (caracteres de controle, espaços, quebras excessivas)
- Chunk adaptativo (single / paragraph / sliding)
- Deduplicação de chunks por hash normalizado
- Metadados enriquecidos em documento e chunks (`contentHash`, `ingestionPipeline`, `chunkStrategy`, etc.)
- Detecção de duplicata por `sourceRef` + `contentHash` na ingestão
- `POST /admin/knowledge/ingest/preview` e pré-visualização no painel (modo texto)
- Correção do `TextChunkerService` (`\n` real em vez de literal `\\n`)

---

## 13. Avaliação de respostas

**Status: Concluído no escopo atual**

### Entregue

- Tabela `ai_response_evaluations` (nota 1-5, veredito, comentário, sugestões)
- Endpoints: candidatos, contexto, salvar/listar avaliações, resumo
- `ResponseEvaluationSuggestionService` (sugestões para conhecimento e diretrizes)
- Aba **Avaliações** no painel admin
- Auditoria `admin.response.evaluated`

---

## 14. Agentes especializados

**Status: Concluído no escopo atual**

### Entregue

- Configuração por agente em `metadata.specialization` (domínio, RAG, diretrizes, tools)
- Presets: RH, TI, Financeiro, Comercial, Jurídico
- RAG filtrado por domínio/namespace/categoria/tag no chat e na simulação
- Diretrizes filtradas por categoria do domínio
- Tools limitadas por agente (`allowedTools`)
- API admin: catálogo, listagem, GET/PUT especialização
- Aba **Agentes** no painel admin

---

## 15. Segurança operacional

**Status: Concluído no escopo atual**

### Entregue

- `ChatInputSecurityService`: sanitização, detecção de prompt injection e score de risco
- Bloqueio no chat (`422 security.input_blocked`) e modo `monitor` (só sinaliza)
- Auditoria: `security.input.blocked`, `security.input.flagged`, `admin.security.scanned`
- API admin: config, resumo 24h, eventos, scan de mensagem
- Aba **Segurança** no painel admin
- Variáveis: `CHAT_INPUT_SECURITY_*`, `CHAT_MESSAGE_MAX_CHARS`

### Modos

- `enforce` (padrão): bloqueia mensagens com risco ≥ limiar
- `monitor`: registra na auditoria sem bloquear

---

# Status consolidado

## Concluído

Itens 1–15 do roadmap admin (incluindo segurança operacional).

## Evoluções futuras

Ver [melhorias-futuras.md](./melhorias-futuras.md): auditoria CSV/timeline, feedback no chat, health por tool, etc.

---

# Próxima ação recomendada

1. Evoluir auditoria (CSV, timeline).
2. Feedback do usuário final no chat (thumbs).
3. Health dedicado por tool.

---

# Regra operacional

Consultar `docs/roadmap/` e `docs/api/` antes de alterar endpoints, migrations ou comportamento do agente.

### Variáveis de métricas LLM e RAG

```env
LLM_PROMPT_TOKEN_COST_PER_1K=0
LLM_COMPLETION_TOKEN_COST_PER_1K=0
LLM_COST_CURRENCY=BRL
RAG_ASSERTIVENESS_MIN_SCORE=0.35
CHAT_INPUT_SECURITY_ENABLED=true
CHAT_INPUT_SECURITY_MODE=enforce
CHAT_MESSAGE_MAX_CHARS=8000
CHAT_INPUT_SECURITY_BLOCK_THRESHOLD=0.7
CHAT_INPUT_SECURITY_FLAG_THRESHOLD=0.35
```

Tabela por provider/modelo (JSON):

```env
LLM_COST_TABLE_JSON=[{"provider":"ollama","model":"qwen2.5:1.5b","promptCostPer1k":0,"completionCostPer1k":0,"currency":"BRL"}]
```
