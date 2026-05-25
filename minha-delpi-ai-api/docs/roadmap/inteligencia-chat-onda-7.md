# Inteligência do chat — Onda 7

**Status:** concluída (maio/2026)  
**Pré-requisitos:** [Onda 6](./inteligencia-chat-onda-6.md)

## Objetivo

Facilitar a **configuração de agentes** no builder (templates de instruções) e ampliar cobertura operacional (OpenAPI + regressão), sem depender de modelo maior.

---

## Entregas da onda

| # | Entrega | Descrição | Status |
|---|---------|-----------|--------|
| 7.1 | Templates de system prompt | Modelos “Operacional TOTVS”, “Documental/RH”, “Documental geral”, “Híbrido” no builder | Concluído (`plugins/minha-delpi-chat/src/domain/agentSystemPromptTemplates.ts`) |
| 7.2 | OpenAPI ampliado | CPV, OTD, giro, compras/vendas produto, listagem OVs | Concluído (`openapi_agent_metadata.py`) |
| 7.3 | Regressão ampliada | Giro, dashboard LMP, vendas produto, OVs, suprimentos diretos | Concluído (+10 casos) |
| 7.4 | Calibração RAG | Guia `rag-context-min-score-calibracao.md` + tabela em `variaveis-de-ambiente.md` | Concluído |
| 7.5 | Homologação latência | Configuração de prod otimizada; medição validada (11s greeting, meta < 15s) | Concluído |
| 7.6 | Seleção OVs vs LMP | Heurística `list_sale_orders` sem confundir com LMP | Concluído |
| 7.7 | Busca por descrição + roteamento | Heurística `product_search`, direct responses (search/OVs), filtros expandidos | Concluído |
| 7.8 | Associação agent_key via context bar | Sessions criadas pelo seletor inferior agora vinculam corretamente o agente | Concluído |

---

## 7.1 — Templates no builder

No **Construtor de agentes** (`ChatAgentBuilderPage`), o campo **Modelo de instruções** aplica um texto base e sugere **estilo de resposta** (`objetivo`, `detalhado`, etc.).

Confirmação antes de substituir instruções já preenchidas.

**Boas práticas após aplicar template operacional:**

1. Anexar `docs/knowledge/api-delpi-rotas-agente.md` à base do agente.
2. Configurar provider OpenAPI `api-delpi` e reimportar schema após deploy da API.
3. Habilitar actions permitidas na especialização do agente.

---

## Correções de seleção de actions (durante a onda)

### Bug: rota de depreciação selecionada para perguntas genéricas

**Causa raiz:** quando `EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED=false`, o fallback genérico selecionava a primeira action candidata (ordem alfabética), sem validar se houve scoring semântico. Adicionalmente, o filtro SQL `path ILIKE '%product%'` capturava rotas de `/production/depreciation_pct`.

**Correções:**

1. `external_action_selection_service.py` — `_select_generic_allowed_action` retorna `None` se o candidato não tem `selectionScore`.
2. `postgres_external_action_repository.py` — filtro alterado para `path ILIKE '%products%'` (plural), excluindo `/production/...`.

### Bug: follow-up de produto sem resolução de código

**Causa raiz:** perguntas como "o que mais pode me dizer sobre o produto?" não eram reconhecidas como referência a produto já mencionado na conversa.

**Correção:** `chat_product_query_intent_service.py` — novo método `_looks_like_product_followup` detecta frases genéricas de follow-up combinadas com termos de produto, resolvendo o código a partir do `conversation_context`.

---

## 7.5 — Homologação de latência em produção

**Servidor:** Intel Xeon Gold 5418Y (4 vCPUs), 7.8 GB RAM, sem GPU.

**Configuração otimizada (maio/2026):**

| Variável | Valor anterior | Valor otimizado | Razão |
|----------|---------------|-----------------|-------|
| `OLLAMA_NUM_THREAD` | 8 | 4 | Alinhar com cores reais (evita context switching) |
| `OLLAMA_MAX_LOADED_MODELS` | 2 | 1 | Libera ~1 GB RAM (reduz swap thrashing) |
| `OLLAMA_NUM_CTX` | 1536 | 1024 | Menos memória por request |
| `LLM_MAX_TOKENS` | 384 | 256 | Menos tokens gerados = inferência mais rápida |

**Resultados medidos:**

| Cenário | Antes | Depois | Meta |
|---------|-------|--------|------|
| Greeting ("olá") | 55s | **11s** | < 15s |
| Consulta operacional (direct response) | — | **< 5s** | < 15s |

**Gargalo residual:** RAM insuficiente (swap ~4 GB esgotado). Recomendação: aumentar RAM do servidor para 16 GB ou mover containers não-essenciais.

---

## 7.7 — Busca de produtos por descrição e melhorias de roteamento

Entrega adicional (maio/2026) para cobrir cenários reais de uso operacional.

| Melhoria | Descrição |
|----------|-----------|
| Heurística `product_search` | Detecta intenção de busca por descrição ("traga 3 exemplos de cabo pp") e roteia para `/products/search` |
| Direct response `product_search` | Formata resultados de busca (código, descrição, tipo, unidade) sem passar pelo LLM |
| Direct response `sale_orders` | Formata lista de OVs (filial, pedido, descrição, data, etapa) |
| Presenter refinado | `ExternalActionResultPresenter` distingue corretamente LMP, OVs e search |
| Filtros no repositório | Termos de busca expandidos (pesquise, traga, exemplos, busque) no filtro de candidatos |
| Prioridade `giro de estoque` | KPI de suprimentos não confunde com rota de produtos |
| OVs genérica vs específica | Prioriza `/sales/` (listagem) sobre `/sales/{code}` (produto específico) |

---

## 7.8 — Associação de agente em sessões via barra de contexto

**Bug:** sessões criadas ao selecionar o agente pelo seletor inferior (context bar) ficavam sem `agent_key`. O sistema não carregava external actions e o LLM respondia genericamente sem acesso ao ERP.

**Causa raiz:** o `requestedAgentKey` passado ao `useChatSession` derivava apenas de `activeAgentPageKey` (navegação à página do agente), ignorando `contextAgentKey` (seletor inferior).

**Correções:**

1. **Frontend (`ChatPage.tsx`):** `requestedAgentKey = activeAgentPageKey ?? contextAgentKey ?? null`
2. **Frontend (`useChatStreaming.ts`):** envia `agentKey` no payload do stream
3. **Backend (stream/send use cases):** se sessão sem `agent_key` e request traz um, atualiza a sessão no banco
4. **Repositório:** novo método `update_session_agent_key`
5. **DB:** sessões existentes sem `agent_key` corrigidas via SQL (`UPDATE 72 rows`)

---

## Próximos passos

1. Reimportar OpenAPI e reindexar `api-delpi-rotas-agente.md` após deploy.
2. Considerar upgrade de RAM do servidor (16 GB) para atingir < 5s em greetings.
3. Onda 8 — a definir (possível: melhoria de contexto conversacional, cache de resultados de actions).

---

## Referências

- [api-delpi-rotas-agente.md](../knowledge/api-delpi-rotas-agente.md)
- [11-guia-agente-chat.md](../../../api-delpi/docs/api/11-guia-agente-chat.md)
- [rag-context-min-score-calibracao.md](./rag-context-min-score-calibracao.md)
- [status-atual.md](../../../docs/12-roadmap-e-evolucao/minha-delpi-chat/status-atual.md)
