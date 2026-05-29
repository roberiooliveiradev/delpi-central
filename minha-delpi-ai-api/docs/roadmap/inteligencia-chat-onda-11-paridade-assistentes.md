# Inteligência do chat — Onda 11: Paridade com ChatGPT/Gemini (roteamento e velocidade)

**Status:** em andamento (maio/2026)  
**Origem:** pergunta de produto em 28/mai/2026 — *«Como o ChatGPT/Gemini sabem qual rota usar nas actions? Pesquise na internet; o modelo está lento e pouco assertivo.»*  
**Pré-requisitos:** [Ondas 1–10](./inteligencia-chat-onda-10.md), [arquitetura chat base](../architecture/chat-intelligence-base.md)

---

## Objetivo

Alinhar o **chat base** (e agentes que o herdam) ao padrão dos assistentes comerciais:

1. **Assertividade** — rota OpenAPI correta sem “spray” de KPIs irrelevantes.  
2. **Velocidade** — menos inferências LLM e menos tokens por turno operacional.  
3. **Previsibilidade** — decisões críticas **antes** do modelo, catálogo pequeno quando o modelo escolhe tool.

> **Regra do projeto:** melhorias de inteligência transversal vão no **chat base** (`minha-delpi-ai-api`), não só no prompt de um agente. Ver `.cursor/rules/chat-intelligence-base.mdc`.

---

## Como ChatGPT e Gemini escolhem a rota (pesquisa 28/mai)

Nenhum deles chama a API sozinho. O fluxo é:

```text
App envia: mensagem + catálogo de tools (nome, descrição, parâmetros JSON Schema)
     ↓
Modelo: responde em texto OU emite tool_call (nome + argumentos)
     ↓
App executa HTTP real e devolve resultado
     ↓
Modelo: resposta final em linguagem natural
```

| Aspecto | OpenAI (ChatGPT) | Google (Gemini) | Implicação para DELPI |
|---------|------------------|-----------------|------------------------|
| Catálogo | Poucas tools bem descritas por turno | Idem + function declarations | Evitar 70+ actions no mesmo prompt |
| Escolha | `tool_choice: auto` / `none` / forçado | Modo function calling equivalente | Default operacional: **não** depender do LLM para rota DELPI |
| Parâmetros | Structured Outputs / `strict` no schema | Schema tipado | Validar `branch`, `code`, datas no backend |
| Latência | 1+ chamadas se usar tools em loop | Idem | Fast path + `direct_answer` sem LLM quando possível |

**Conclusão da pesquisa:** para ERP/DELPI, o equivalente saudável é **heurística determinística** (`ExternalActionSelectionService`) + **opcional** loop agentic com catálogo filtrado — não enviar todo o OpenAPI ao LLM em todo turno.

Referências externas (consultadas na sessão 28/mai):

- [OpenAI — Function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [Google — Function calling (Gemini API)](https://ai.google.dev/gemini-api/docs/function-calling)

---

## Arquitetura alvo (DELPI)

```text
Mensagem
  → normalização + typos
  → ChatIntelligencePipelineService (análise / refinamento / skip_rag)
  → ExternalActionSelectionService (rota DELPI ANTES do LLM)
  → [opcional] ChatAgenticToolLoopService (só se habilitado + catálogo ≤ N)
  → direct_answer / presenter OU RAG + LLM enxuto
```

| Camada | Papel | Default maio/2026 |
|--------|--------|-------------------|
| `ExternalActionSelectionService` | Intent → action OpenAPI | Sempre ativo no fast path |
| `ChatOperationalParameterService` | Pede código quando falta | `direct_answer`, sem API |
| `ChatOperationalRefinementService` | Follow-up filial/armazém pós-estoque/KPI/suprimentos | Reconsulta com parâmetros |
| `ChatRouteContextService` | Herança de segmento de rota (`/purchases`, `/cpv`, …) no histórico | Multi-turno sem repetir código/intent |
| `ChatAgenticToolLoopService` | Planner LLM + tools extras | **`CHAT_AGENTIC_LOOP_ENABLED=false`** |
| `CHAT_TOOL_ROUTER_ENABLED` | Router LLM de tools internas | **`false`** |
| `ChatAssistantIdentityService` | «Quem te criou?» | **`CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED=true`** |

---

## O que já foi feito (código + commits)

### Sessão de pesquisa 28/mai (implementação na branch `chat`)

| Commit | Entrega | Critério |
|--------|---------|----------|
| `89233b6b` | Identidade do assistente em resposta direta (sem LLM/RAG) | Latência baixa em CPU |
| `787baffc` | RAG de identidade filtrado + fallback canônico | Sem doc `Normas_Tecnicas_*` em «quem te criou» |
| `f10d7250` | Estoque **sem código** → pede código; sem ROL; sem loop agentic | Não dispara KPI comercial por fallback |
| `a1128dc5` | Multi-action só com códigos da **mensagem atual** | Não reexecuta N produtos do histórico |
| `a557608c` | `ChatOperationalRefinementService` — «filtre filial 02» após estoque | `branch` na action, `skip_rag` |
| `3fe0cd39` | Smoke operacional com histórico isolado | 6/6 cenários |
| `5a22ab5d` | Script `smoke_operational_questions.py` | Perguntas reais |

| `5d020d7b` | Consolidação paginada + datas/ROL (`ChatPaginationConsolidationService`, `ChatDateRangeIntentService`) | «traga tudo» / «sim, continue» consolidam páginas; «rol do mês de março» resolve período |
| *(working tree)* | Formato na consolidação (tabela/árvore/gráfico) + herança de `preferredFormat` | «tabela completa» após consulta parcial |

Documentação parcial já em [`chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) (seções parâmetro obrigatório, loop agentic, refinamento, **consolidação paginada**).

### Outras conversas relacionadas (não confundir com Onda 11)

| Pedido | Documento |
|--------|-----------|
| Canvas / tabelas / gráficos estilo ChatGPT (25/mai) | [apresentacao-rica-chat-onda-9.md](./apresentacao-rica-chat-onda-9.md) — **concluída** |
| Auditoria rota a rota api-delpi | [api-delpi-chat-intelligence-audit.md](./api-delpi-chat-intelligence-audit.md) |
| Pesquisa na internet (`web_search`) | **Sem onda dedicada** — ver backlog §11.6 abaixo |

### Infra / auth (conversa 28/mai tarde — desbloqueio do portal, não é Onda 11)

| Commit | Entrega |
|--------|---------|
| `b41336a0` | Nginx dev: `X-Forwarded-*` no `/auth/`; redirect URI estável; `checkLoginIframe` só em PROD |
| `7bf1b11e` | `jwt_validator`: usa `KEYCLOAK_JWKS_URL` (fix 401 em `/core-api/me` → loop de login) |

Bug de JWKS introduzido em `a2b0e107` (09/mar/2026 — discovery apontava `localhost:8080` dentro do Docker); **exposto** quando o login SSO passou a completar após fixes de infra.

---

## O que falta (backlog Onda 11)

### 11.1 — Roteamento e assertividade (prioridade alta)

| # | Item | Status | Critério de pronto |
|---|------|--------|-------------------|
| 11.1.1 | Estender refinamento operacional além de estoque (estrutura, parents, KPI com filial) | ✅ | CPV/suprimentos e KPIs departamentais com «filial 02»; sub-rotas produto (`purchases`, `suppliers`, …) com herança de segmento; estoque multi-produto mantido |
| 11.1.2 | Datas automáticas em KPIs e OV (`start_date`/`end_date`) | ✅ | `ChatDateRangeIntentService` + merge em suprimentos/KPIs e listagem `/sales`; datas `DD/MM/YYYY` não viram código de produto |
| 11.1.3 | Heurística explícita `summary` vs `analyser` | ✅ | Intent `SUMMARY` + rank dedicado; regressão «resumo do produto 10080047» |
| 11.1.4 | Regressão E2E send/stream com histórico (filtre filial, estoque desse produto) | ✅ | `test_chat_stock_refinement_stream_send.py` + `test_chat_turn_preparation_stock_refinement.py` |
| 11.1.5 | Reimport OpenAPI + reindexar `api-delpi-rotas-agente.md` pós-deploy api-delpi | ✅ | `scripts/sync_api_delpi_openapi.py` + catálogo `_generated/` + guia RAG atualizado |

### 11.2 — Velocidade e prompt (prioridade alta)

| # | Item | Status | Critério de pronto |
|---|------|--------|-------------------|
| 11.2.1 | Garantir `skip_rag` + sem LLM em todos os direct answers operacionais | ✅ | Guarda `direct_answer` → `skip_rag`; teste `test_chat_turn_preparation_direct_answer_skip_rag.py` |
| 11.2.2 | Calibrar `LLM_MAX_TOKENS` / `OLLAMA_NUM_CTX` por ambiente (homologação &lt; 15s) | ✅ | `CHAT_LLM_LATENCY_PROFILE` (`operational_cpu`, `balanced`, `documental`); checklist em [rag-context-min-score-calibracao.md](./rag-context-min-score-calibracao.md) |
| 11.2.3 | Portal: bootstrap sem `login()` em loop se `/me` falhar (guard + `stripOAuthHash`) | ✅ | 401 no bootstrap limpa sessão; `stripOAuthHash` após redirect Keycloak |
| 11.2.4 | Compose dev: volume `../shared:/shared` no `core-api` | ✅ | Fix JWT sobrevive a `recreate` sem `docker cp` |

### 11.3 — Tool-calling “estilo GPT” (prioridade média, sandbox)

| # | Item | Status | Critério de pronto |
|---|------|--------|-------------------|
| 11.3.1 | Catálogo por intent (≤12 actions) no loop agentic | 🟡 | `CHAT_AGENTIC_CATALOG_MAX_ACTIONS` + `find_candidate_actions` |
| 11.3.2 | Schemas OpenAPI enxutos por action (descrição + exemplos) | ⬜ | Melhora ranker e planner quando agentic ligado |
| 11.3.3 | `CHAT_NATIVE_TOOL_CALLING_ENABLED` só em agentes piloto | ⬜ | Tools internas via LLM; OpenAPI continua heurístico |
| 11.3.4 | Métricas `intelligence.timings` por turno no admin | 🟡 | Já existe Onda 5; validar em homologação |

### 11.4 — Qualidade de resposta pós-tool (prioridade média)

| # | Item | Status | Critério de pronto |
|---|------|--------|-------------------|
| 11.4.1 | Resposta direta pós-tool operacional sem re-sumarizar no LLM | ✅ | `prefer_presentation_direct_answer` + `skip_rag`; apresentação rica sem markdown duplicado |
| 11.4.2 | Fase 6 Onda 9: drill-down na tabela («detalhe linha X») | ✅ | `onDrillDown` em `ChatPage`/`ChatMessageList`; `sendMessage({ content })`; queries filial/código |
| 11.4.3 | Apresentação rica sem texto duplicado (tabela/gráfico + markdown) | ✅ | `_compact_direct_answer_for_rich_presentation` + `shouldSuppressMarkdownForPresentation` |
| 11.4.4 | Consolidação paginada automática (total/completo/continuar) | ✅ | `ChatPaginationConsolidationService` + múltiplas chamadas API; limite por turno + confirmação; tabela/árvore/listagem |

### 11.5 — Observabilidade e operação

| # | Item | Status | Critério de pronto |
|---|------|--------|-------------------|
| 11.5.1 | Smoke operacional no CI ou script pós-deploy | ✅ | `scripts/run_onda11_validation.sh` (pytest + smoke); checklist manual #56–60 |
| 11.5.2 | Expor `knowledgeDocumentMaxChars` em `GET /chat/capabilities` | ✅ | Front valida antes do upload |

### 11.6 — Fora do escopo imediato (registrar para onda futura)

| Tema | Notas |
|------|--------|
| **Pesquisa na internet** | Tool interna `web_search` (não action OpenAPI); política de fontes; ver discussão na conversa (~msg «pesquisa na internet») |
| **RBAC perfis formais** | [melhorias-futuras.md](./melhorias-futuras.md) — core-api |
| **Rotas NC PostgreSQL** | [api-delpi-chat-intelligence-audit.md](./api-delpi-chat-intelligence-audit.md) backlog #3 |

---

## Variáveis de ambiente (referência)

| Variável | Default | Onda 11 |
|----------|---------|---------|
| `CHAT_AGENTIC_LOOP_ENABLED` | `false` | Manter off em prod até 11.3 validado |
| `CHAT_TOOL_ROUTER_ENABLED` | `false` | Manter off |
| `CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED` | `true` | Manter on |
| `CHAT_OPERATIONAL_SLIM_USER_CONTEXT` | `true` | Manter on em operacional |
| `CHAT_AGENTIC_CATALOG_MAX_ACTIONS` | `12` | Revisar com 11.3.1 |
| `CHAT_PAGINATION_AUTO_FETCH_ENABLED` | `true` | Consolidação paginada (11.4.4) |
| `CHAT_PAGINATION_MAX_PAGES_PER_TURN` | `5` | Páginas por turno antes de pedir confirmação |
| `CHAT_LLM_LATENCY_PROFILE` | `balanced` | Preset `operational_cpu` / `documental` para `LLM_MAX_TOKENS` + `OLLAMA_NUM_CTX` |

---

## Critérios de aceite da Onda 11

- [x] Smoke operacional **6/6** (ou ampliado) verde no container após deploy.  
- [x] «estoque do produto» sem código → pede código, **sem** ROL/loop.  
- [x] «estoque 10080022» → `/stock`; «filtre filial 02» → `/stock?branch=02` (com `agentKey` na sessão).  
- [x] «quem te criou?» → resposta canônica em &lt; 2s (CPU) sem dump de prompt no chat.  
- [x] Login portal + `/core-api/me` **200** com token válido (JWKS interno).  
- [x] Documento vigente (este arquivo) referenciado no README do roadmap.

---

## Validação rápida

```bash
# Regressão inteligência
docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api pytest \
  tests/unit/domain/services/test_chat_intelligence_regression.py \
  tests/unit/domain/services/test_chat_operational_refinement_service.py \
  tests/unit/application/services/test_external_action_selection_service.py -q

# Sincronizar OpenAPI api-delpi (pós-deploy)
docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
  python scripts/sync_api_delpi_openapi.py

# Smoke operacional
docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
  python scripts/smoke_operational_questions.py

# Validação completa Onda 11 (pytest + smoke)
docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
  bash scripts/run_onda11_validation.sh

# Auth (host)
curl -s -X POST 'http://localhost/auth/realms/delpi/protocol/openid-connect/token' \
  -d 'grant_type=password&client_id=delpi-central&username=rober&password=***' | jq -r .access_token | head -c 20
# depois GET /core-api/me com Bearer → 200
```

---

## Histórico deste documento

| Data | Alteração |
|------|-----------|
| 2026-05-28 | Criação: consolida pesquisa ChatGPT/Gemini (28/mai), commits da branch `chat`, backlog e itens da conversa (login/JWKS). |
| 2026-05-29 | Revisão Onda 11: regressão 145+ testes, smoke 6/6, multi-turn 9/9, E2E HTTP estoque→filial com agente; drill-down path template corrigido. |
| 2026-05-29 | Consolidação paginada (11.4.4): total/completo/continuar em tabela, árvore e demais listagens; docs + variáveis `CHAT_PAGINATION_*`. |
| 2026-05-29 | 11.1.5: `sync_api_delpi_openapi.py`, catálogo gerado 83 rotas, guia RAG revisado (ROL, produção, propostas). |
| 2026-05-29 | 11.2.2/11.4.1/11.5.1: `CHAT_LLM_LATENCY_PROFILE`, `prefer_presentation_direct_answer`, `run_onda11_validation.sh`. |

---

## Próxima onda

Quando 11.1–11.2 estiverem estáveis em homologação, abrir **Onda 12** para `web_search` + política de citações, ou fundir itens 11.6 conforme prioridade de produto.
