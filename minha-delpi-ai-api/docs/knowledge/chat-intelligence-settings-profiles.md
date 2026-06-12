# Perfis de configuração — Inteligência do chat

Referência para **Admin → Inteligência do chat** (`ChatIntelligenceSettingsService`), alinhada ao pipeline do agente **minha-delpi-chat** (roteamento determinístico + RAG + fast paths operacionais).

**Onde configurar:** painel admin do plugin Minha DELPI Chat → seção *Inteligência do chat*.

**Arquitetura relacionada:** [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) (defaults conservadores: router e agentic **desligados**).

**Smoke operacional:** [`../testing/smoke-operacional-manual.md`](../testing/smoke-operacional-manual.md).

---

## Legenda

| Símbolo | Significado |
|---------|-------------|
| ✅ | Ligado |
| ❌ | Desligado |
| — | Valor numérico (quando o toggle está irrelevante) |

**Defaults do código** (quando o admin não sobrescreve): router ❌, agentic ❌, RAG híbrido ✅, rerank ✅, FTS ✅, ranking semântico ✅, resumo histórico ✅.

O painel admin **persiste em runtime** (`chat_intelligence_settings`); variáveis de ambiente abaixo servem como bootstrap ao subir o container.

**Outros bundles de plataforma** (modos de resposta, visão, pipeline de aprendizagem): ver [`chat-admin-platform-settings.md`](chat-admin-platform-settings.md).

---

## 1. Recuperação de conhecimento (RAG)

| Configuração | Dev (local / Ollama) | Produção | Observação |
|--------------|----------------------|----------|------------|
| **RAG híbrido** (vetor + palavras-chave) | ✅ | ✅ | Essencial para códigos, SC2010, grupos 1008, SKUs |
| **FTS Postgres** | ✅ | ✅ | Só faz sentido com híbrido ligado |
| **Rerank pós-híbrido** | ❌ ou ✅ | ✅ | Desligar em dev economiza ~200–500 ms; em prod melhora precisão |
| **Score mínimo RAG** | **0,35** | **0,35–0,40** | Default `0,35`. Subir para 0,40 se o prompt vier com ruído |

---

## 2. Actions e APIs externas

| Configuração | Dev | Produção | Observação |
|--------------|-----|----------|------------|
| **Ranking semântico de actions** | ✅ | ✅ | Ajuda com catálogo OpenAPI grande |
| **Score mínimo action semântica** | **0,42** | **0,42** | Default do código; complementa regras determinísticas |
| **Reindexar embeddings** | Após criar/editar actions | Idem | Botão do painel — necessário se ranking estiver ✅ |

---

## 3. Orquestração do LLM

| Configuração | Dev | Produção | Observação |
|--------------|-----|----------|------------|
| **Router LLM de ferramentas** | ❌ | ❌ | +1 LLM/turno; pipeline já roteia estoque, SQL, Normas |
| **Tool-calling nativo** (vLLM/Ollama) | ❌ | ❌ | Testar isoladamente; conflita com router/agentic |
| **Loop agentic** | ❌ | ❌ (ou ✅ pontual) | Causa comum de lentidão em perguntas documentais (ex.: N1) — o pipeline **pula** agentic em intent Normas (`ChatTechnicalDescriptionIntentService`) |
| **Máx. passos agentic** | — (se ❌) | **1** (se ✅) | Só para fluxo multi-etapa raro; evitar 2+ em prod sem monitorar |

---

## 4. Contexto da conversa

| Configuração | Dev | Produção | Observação |
|--------------|-----|----------|------------|
| **Resumo de histórico longo** | ✅ | ✅ | Entra após ~16 mensagens; não afeta turnos curtos de smoke |

---

## Resumo em uma linha

| Perfil | RAG | Actions | Orquestração | Histórico |
|--------|-----|---------|--------------|-----------|
| **Dev** | híbrido ✅ FTS ✅ rerank ❌ score **0,35** | rank ✅ score **0,42** | router ❌ agentic ❌ nativo ❌ | resumo ✅ |
| **Produção** | híbrido ✅ FTS ✅ rerank ✅ score **0,35–0,40** | rank ✅ score **0,42** | router ❌ agentic ❌ nativo ❌ | resumo ✅ |

---

## Variáveis de ambiente (bootstrap)

| Variável | Dev sugerido | Prod sugerido |
|----------|--------------|---------------|
| `CHAT_AGENTIC_LOOP_ENABLED` | `false` | `false` |
| `CHAT_TOOL_ROUTER_ENABLED` | `false` | `false` |
| `CHAT_RAG_HYBRID_ENABLED` | `true` | `true` |
| `CHAT_RAG_RERANK_ENABLED` | `false` | `true` |
| `CHAT_RAG_FTS_ENABLED` | `true` | `true` |
| `CHAT_NATIVE_TOOL_CALLING_ENABLED` | `false` | `false` |
| `CHAT_HISTORY_SUMMARY_ENABLED` | `true` | `true` |
| `EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED` | `true` | `true` |
| `RAG_CONTEXT_MIN_SCORE` | `0.35` | `0.35` |
| `EXTERNAL_ACTION_SEMANTIC_MIN_SCORE` | `0.42` | `0.42` |
| `CHAT_OPERATIONAL_FAST_PATH_ENABLED` | `true` | `true` |

Após alterar `.env` / compose, recrie o container (`--force-recreate minha-delpi-ai-api`). O boot executa `sync-chat-intelligence-env`: o **runtime e o painel admin** passam a refletir o `.env` (env tem prioridade sobre toggles antigos no Postgres).

---

## Latência esperada por turno (ordem de grandeza)

| Perfil | Normas (N1: «como descrever um terminal?») | Operacional (G4: estoque com código) |
|--------|---------------------------------------------|--------------------------------------|
| **Dev recomendado** | RAG + **1 LLM** | fast path + **0–1 LLM** |
| **Router + agentic ligados** | RAG + router + agentic + **2–4 LLMs** | idem |

---

## Diagnóstico: «nenhum trecho adicional aplicável»

Em perguntas de **Normas** (N1–N14), fontes com escopo **global** (`company-knowledge`) entram no **prompt do LLM**, mas podem **não aparecer** na lista de fontes visíveis ao usuário (`ChatSourceVisibilityService`). Com router/agentic desligados, o stream mostra *«contexto aplicado (N caracteres)»* quando há RAG global sem fontes visíveis.

---

## Quando ligar algo extra (exceções)

| Cenário | O que ligar |
|---------|-------------|
| Sandbox: fluxos multi-etapa («busque produto X e depois estoque») | Agentic ✅, **máx. 1 passo** |
| Agente com muitas actions e erros de rota frequentes | Preferir melhorar descrições + ranking; router ⚪ só em teste |
| Base RAG grande com respostas genéricas | Rerank ✅ + score RAG **0,40** |
| Modelo vLLM com tool-calling nativo estável | Nativo ⚪ — **desligar** router e agentic antes de testar |

---

## Checklist antes do smoke

1. Conferir perfil **dev** ou **prod** acima.
2. **Salvar configurações** no admin.
3. Se alterou actions: **Reindexar embeddings**.
4. Rodar [`smoke-operacional-manual.md`](../testing/smoke-operacional-manual.md) ou `scripts/smoke_gpt_instructions_improvements.py`.

---

*Última revisão: maio/2026 — agente minha-delpi-chat, pipeline pós-entregas Normas/SQL.*
