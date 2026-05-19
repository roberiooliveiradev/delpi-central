# Inteligência do chat — Onda 6

**Status:** concluída (maio/2026) — validação de latência &lt; 15s em homologação pendente  
**Pré-requisitos:** [Ondas 1–5](./inteligencia-chat-onda-1.md)

## Objetivo

Voltar ao modelo leve **`qwen2.5:1.5b`** (latência baixa em CPU) e concentrar ganhos de qualidade no **software** (pipeline), não em parâmetros maiores do LLM.

**Estratégia:** escolher a fonte certa (action, RAG, tools), formatar bem o retorno da API e chamar o LLM só quando for indispensável.

---

## Pipeline de referência

```text
Mensagem → Segurança → Agente/projeto (system prompt)
         → Seleção de action (heurística + FTS; semântico opcional)
         → execute_external_action → resposta direta (sem LLM) quando ok
         → ou RAG (keyword/FTS) → LLM (1.5b)
```

Serviços principais:

| Etapa | Código |
|-------|--------|
| Fast path cumprimento | `ChatFastPathService` |
| Fast path operacional | `ChatOperationalPipelineService` |
| Seleção de action | `ExternalActionSelectionService` |
| Resposta sem LLM | `ChatExternalActionDirectResponseService` + `ChatProductQueryIntentService` |
| Montagem do prompt | `ChatPromptBuilderService` + `PromptPolicyService` |
| RAG | `RagContextService` |

---

## Entregas da onda

| # | Entrega | Descrição | Status |
|---|---------|-----------|--------|
| 6.1 | Modelo padrão 1.5b | Defaults em `settings.py`, Compose e `.env.prod` | Concluído |
| 6.2 | Fast path operacional | Produto/estoque/LMP: pula RAG/resumo pesado quando aplicável | Concluído |
| 6.3 | Seleção de actions | Heurísticas + FTS; ranking semântico opcional | Concluído |
| 6.4 | Resposta direta | Templates após `execute_external_action` (produto, LMP, SQL, genérico) | Concluído |
| 6.5 | Prompts por tipo de agente | Operacional vs documental; instruções enxutas em CPU | Concluído (`operational-agent.md`, `api-delpi-routes.md`, doc RAG) |
| 6.6 | RAG enxuto | Keyword/FTS; hybrid/rerank desligados em prod CPU | Config ok |
| 6.7 | Observabilidade | `intelligence.timings`; action escolhida + motivo | Concluído |
| 6.8 | Regressão | Fixtures com 15–20 perguntas reais da operação | Concluído (`tests/fixtures/chat_intelligence_regression_cases.py`) |

---

## Melhorias detalhadas (backlog priorizado)

### 1. Resposta direta após action (alto impacto)

**Problema:** Qualidade e latência dependem do LLM formatar JSON que a API já devolveu.

**Ações:**

- Templates por tipo de action (produto, estoque, LMP, SQL, genérico).
- Tabela curta para estoque (filial \| quantidade) em vez de lista longa.
- Mensagens claras para `0 registro(s)` e erros HTTP (evitar cair no LLM com JSON bruto).
- Reforçar follow-up: “e o estoque?”, “desse produto” via `ChatProductQueryIntentService.resolve_product_code` + histórico.

**Arquivos:** `chat_tool_context_service.py`, `chat_product_query_intent_service.py`, `external_action_result_presenter` (se existir).

### 2. Seleção de actions (alto impacto)

**Ações:**

- Sinônimos: referência, ref, SKU, material, MP, insumo, saldo, posição, OV, ordem de venda.
- Códigos com máscara (`10.080.055`) ou &lt; 4 dígitos, se a operação usar.
- LMP: lista de materiais, amostra, além de “lmp”.
- Metadado `intelligence.selectedAction` com `reason` (debug no admin).
- Manter `EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED=false` em CPU; homologar com `true` só se heurística falhar muito.

**Arquivos:** `external_action_selection_service.py`, `postgres_external_action_repository.py`.

### 3. Fast path operacional (velocidade)

**Ações:**

- Ampliar termos em `ChatOperationalPipelineService._OPERATIONAL_TERMS`.
- Não ativar modo leve em pergunta mista (ex.: “explique o processo e estoque do 10080055”) — exigir intenção + código quando possível.
- Garantir tentativa de action antes do LLM quando `allowedActionIds` não estiver vazio.

**Arquivos:** `chat_operational_pipeline_service.py`, use cases stream/send.

### 4. Prompts e agentes (qualidade percebida)

**Ações:**

- Templates de system prompt no admin: “Operacional TOTVS”, “Documental/RH”.
- Prompt base mais curto em modo operacional (menos tokens no 1.5b).
- Regra explícita: se a ferramenta já retornou dados, não repetir JSON nem pedir o que já foi informado.

**Arquivos:** `chat_prompt_builder_service.py`, `prompt_policy_service`, gestão de agentes (UI).

### 5. RAG (quando não for action)

**Ações:**

- Calibrar `RAG_CONTEXT_MIN_SCORE` com admin RAG test.
- Melhorar ingestão de documentos operacionais (chunking já existe em `KNOWLEDGE_*`).
- Não ligar hybrid/rerank em prod CPU até GPU ou baseline estável.

### 6. Medição

**Ferramentas existentes:**

- `GET /admin/metrics/summary` e `intelligence.timings` (`ragMs`, `toolsMs`, `llmMs`).
- Feedback thumbs nas mensagens.
- Simulação admin com `sessionId` real.

**Critério:** bateria de 15–20 perguntas reais — action correta, resposta direta aceitável, &lt; 15s em CPU prod.

---

## Ordem de implementação sugerida

| Ordem | Item | Esforço estimado |
|-------|------|------------------|
| 1 | Fixtures + testes (perguntas reais) | 1–2 dias |
| 2 | Templates resposta direta (LMP + genérico) | 1 dia |
| 3 | Sinônimos e códigos na seleção de actions | 1 dia |
| 4 | `intelligence` com action + motivo | 0,5 dia |
| 5 | Templates system prompt por tipo de agente | 1 dia |
| 6 | Ajuste fino RAG (score + ingestão) | contínuo |

---

## Modelo vs pipeline

| Abordagem | Quando usar |
|-----------|-------------|
| `qwen2.5:1.5b` (default) | Produção CPU — inteligência via actions + RAG + prompts |
| `qwen2.5:3b` | Homologação pontual se redação final ainda fraca **após** itens 1–5 |
| `vllm` + GPU | Futuro — modelo maior com latência aceitável |

---

## Variáveis (produção CPU recomendadas)

| Variável | Valor sugerido |
|----------|----------------|
| `OLLAMA_MODEL` | `qwen2.5:1.5b` |
| `OLLAMA_NUM_CTX` | `1536` |
| `LLM_MAX_TOKENS` | `384` |
| `CHAT_SESSION_TITLE_LLM_ENABLED` | `false` |
| `CHAT_OPERATIONAL_FAST_PATH_ENABLED` | `true` |
| `CHAT_EXTERNAL_ACTION_DIRECT_RESPONSE_ENABLED` | `true` |
| `EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED` | `false` |
| `CHAT_RAG_HYBRID_ENABLED` | `false` |
| `CHAT_RAG_PREFER_KEYWORD_SEARCH` | `true` |
| `CHAT_TOOL_ROUTER_ENABLED` | `false` |
| `CHAT_HISTORY_SUMMARY_ENABLED` | `false` |
| `CHAT_NATIVE_TOOL_CALLING_ENABLED` | `false` |

### O que evitar em CPU (por enquanto)

| Flag | Motivo |
|------|--------|
| `CHAT_TOOL_ROUTER_ENABLED=true` | LLM extra antes de cada resposta |
| `CHAT_RAG_HYBRID_ENABLED=true` | embedding `bge-m3` em toda pergunta |
| `CHAT_NATIVE_TOOL_CALLING_ENABLED=true` | loop de tools + latência |
| `CHAT_HISTORY_SUMMARY_ENABLED=true` | outra chamada LLM |
| `qwen2.5:3b` sem necessidade | latência; usar só após esgotar pipeline |

---

## Critérios de aceite

- [x] Defaults do repositório apontam para `qwen2.5:1.5b`
- [ ] Pergunta operacional típica (estoque por código) &lt; 15s em CPU de produção (validar em homologação)
- [x] Pergunta documental usa RAG sem embedding em toda mensagem (keyword/FTS) — flags prod
- [x] Metadados `intelligence` indicam fast path / resposta direta quando aplicável
- [x] Bateria de regressão (fixtures) verde para produto, estoque, follow-up e LMP

---

## Documentos relacionados

- [melhorias-futuras.md](./melhorias-futuras.md) — melhorias **admin/UI** (feedback, métricas, simulação); **não** cobre pipeline de inteligência
- [status-atual.md](../../../docs/12-roadmap-e-evolucao/minha-delpi-chat/status-atual.md) — visão plataforma
- [variaveis-de-ambiente.md](../../../docs/02-infraestrutura/variaveis-de-ambiente.md) — env IA
