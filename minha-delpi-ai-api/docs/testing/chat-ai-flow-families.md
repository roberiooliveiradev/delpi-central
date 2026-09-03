# Famílias de fluxo do chat — testes de IA (canônico)

| Campo | Valor |
|-------|--------|
| **Path canônico** | `docs/testing/chat-ai-flow-families.md` |
| **Nome anterior** | `docs/roadmap/audit-chat-base-familias-fluxos-set2026.md` (redirecionamento legado) |
| **Famílias** | F01–F24 (+ F25+ conforme § 0.3) |
| **Critérios** | R1–R8 (§ 1.1) |

> **Documento canônico — testes de IA do chat**  
> Toda mudança de **inteligência**, **fluxo de turno**, **skill**, **roteamento operacional** ou **apresentação** no chat base deve ser **mapeada aqui** antes do merge (roteiro § 3, planilha § 5, critérios R1–R8).  
> Complementa (não substitui): [`chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) (arquitetura), [`api-delpi-chat-intelligence-audit.md`](../roadmap/api-delpi-chat-intelligence-audit.md) (rotas api-delpi), [`docs/flows/`](../flows/) (mapa HTTP).

**Objetivo:** inventário acionável para caçar bugs/gaps por família, com **roteiros de usuário** (PT-BR) prontos para smoke live.  
**Escopo:** chat base (`minha-delpi-ai-api`) + MFE `plugins/minha-delpi-chat` + skills/agentes.  
**Princípio:** inteligência transversal no chat base; agentes só filtram actions/skills/prompt (`docs/architecture/chat-intelligence-base.md`).

**Status deste doc**

| Item | Estado |
|------|--------|
| Inventário + roteiros | ✅ pronto |
| Unitários das regressões recentes (agente / SQL authoring / leak) | ✅ verdes (set/2026) |
| Smoke domain + HTTP F01 / F04 / F03 | ✅ **18/18 PASS** (set/2026) — `scripts/smoke_chat_flow_families_f01_f04_f03.py` |
| Bateria interação humana simulada (HTTP + R1–R8) | ✅ script `scripts/human_interaction_battery_live.py` — rodar em stack live |
| Smoke live UI (demais famílias § 5) | ⏳ pendente |

**Mitigações recentes (já no código — revalidar no live):**

- Help/ativação de agente ≠ fluxo produto; «consulta» solta ≠ SQL.
- Authoring SQL (`crie/monte SQL`) **bloqueia** REST operacional (ex.: programação).
- Follow-up top N não troca família Protheus (SB↔SA).
- Strip de leak do especialista SQL + marcadores em `llm_synthesis_delivery.json`.
- TV: `monte+tabela` não sequestra SQL fora do surface.

---

## 0. Governança — novos fluxos e alterações (obrigatório)

Este arquivo é a **fonte única** para planejar e registrar testes de IA do chat. Não abrir PR de inteligência/fluxo sem atualizar o mapeamento abaixo.

### 0.1 Quando atualizar (gatilhos)

| Mudança no código/produto | Ação neste doc |
|---------------------------|----------------|
| Nova intenção, sub-intent, heurística ou policy JSON | § 3 (família existente ou **F25+** na § 2) + fixture em `chat_intelligence_regression_cases.py` |
| Nova rota api-delpi consumida pelo chat | Família **F03** (ou F06/F17…) + `operational_route_registry.json` + roteiro § 3 |
| Nova skill ou action de agente | § 4 (skills) + § 3 da família + allowed actions |
| Novo fluxo UI (toolbar, formato, ativação agente) | Família **F01/F13/F22** + roteiro manual § 8.2 |
| Fix de bug reportado em conversa | Linha na planilha § 5 + caso na bateria § 1.3 (se reproduzível via HTTP) |
| Alteração de latência / turn analysis / skip tools | R8 § 1.4 + re-run bateria ou `SMOKE_ONLY` |
| Novo surface (TV, PAC, anexo, simulate) | Família dedicada § 3 + marcar `optional` na bateria se HTTP não couber |

### 0.2 Checklist por PR (inteligência / chat)

1. **Família** — qual Fxx? Se nenhuma couber, adicionar linha em § 2 e bloco em § 3.
2. **Roteiros** — pelo menos 2 frases PT-BR (canônica + variação humana: typo/abreviação/follow-up).
3. **R1–R8** — quais dimensões são obrigatórias para essa família (tabela § 1.1).
4. **Automação** — unitário/fixture **e** (quando possível) caso em `human_interaction_battery_live.py` ou smoke da família.
5. **Planilha § 5** — nova linha ou atualizar veredito/evidência.
6. **Não duplicar** — regra transversal no chat base; não criar checklist só no prompt do agente.

### 0.3 Nova família (F25+)

1. Atribuir ID `F25`, nome, superfície crítica na tabela § 2.
2. Criar § 3 com: **Esperado**, **Roteiros** (≥3), **Gaps**, **Âncoras** (serviços/paths reais).
3. Registrar dimensões obrigatórias na tabela § 1.1.
4. Adicionar linhas em § 5 e, se automatizável, entradas em `_cases_catalog()` do script § 1.3.

### 0.4 O que este doc não cobre

| Tema | Documento canônico |
|------|-------------------|
| Contrato HTTP / OpenAPI api-delpi | [`api-delpi-chat-intelligence-audit.md`](../roadmap/api-delpi-chat-intelligence-audit.md), `new-api-route-checklist.mdc` |
| Mapa de endpoints e pipeline send/stream | [`docs/flows/`](../flows/) |
| Arquitetura de serviços | [`chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) |
| Homologação manual operacional legada | [`smoke-operacional-manual.md`](./smoke-operacional-manual.md) |

---

## 1. Como usar este audit

1. Escolher uma **família** (Fxx).
2. Rodar os **roteiros** em: chat comum → agente Minha DELPI → (se couber) projeto / simulate admin.
3. Avaliar cada caso com os **critérios R1–R8** (§ 1.1) e **latência/gargalos** (§ 1.4) — obrigatório antes de marcar veredito.
4. Marcar na tabela § 5: `PASS` / `FAIL` / `WARN` / `N/A` + evidência (operationId, intentRoute, dimensões R1–R8).
5. FAIL → causa raiz no **módulo canônico** da família (não patch no MFE/agente).

### 1.1 Critérios de análise (R1–R8) — obrigatório em todo smoke live

Toda análise (humana ou ticket) **deve** preencher as dimensões abaixo. Não basta «a resposta pareceu boa»: sem evidência em metadata/admin, o caso fica **inconcluso** (tratar como WARN até re-testar).

| ID | Dimensão | O que verificar | Fonte de evidência | PASS | FAIL típico |
|----|----------|-----------------|-------------------|------|-------------|
| **R1** | **Roteamento** | Família Fxx correta; `intentRoute`, `decision`, `subIntent` | Admin: intent / turn analysis | Bate § 3 da família | Intent certo + família errada (help → SQL, normas → cadastro) |
| **R2** | **Tools / trajectory** | Quantidade, tipo e ordem de tools; skip quando devido | `toolCount`, `toolCalls[]`, `skipTools` | 0 tools no comum/identity; tool certa com agente | ERP sem agente; tool errada; tool sem pedido |
| **R3** | **Parâmetros / slots** | Código, filial, período, grounding | Args da tool, `operationalFocus`, slots | Só pede o que falta; não inventa | Clarify genérico com dado na frase; código/rota errados |
| **R4** | **Conteúdo / utilidade** | Responde à pergunta; PT-BR; sem desvio de família | Bolha + prosa | Resposta útil e coerente | «Reformule», outra família, inglês indevido, alucinação óbvia |
| **R5** | **Apresentação** | Formato (texto / tabela / gráfico / painel) | `presentationDecision`, painel MFE | Alinhado ao pedido e ao contrato API | Formato errado; duplicata KPI+tabela; MFE redecide formato |
| **R6** | **Grounding / follow-up** | Usa último resultado quando aplicável | `groundingStatus`, `turnGroundingStage`, histórico | Refino coerente («em tabela», filial, período) | Pega entidade/tool errada do histórico |
| **R7** | **Paridade de superfície** | send ≈ stream ≈ simulate (quando testado) | Compare admin / simulate | Mesmo intent e tool path | Simulate sem `previous_messages` inventa contexto |
| **R8** | **Performance / latência** | Tempo total e **gargalo dominante** (§ 1.4) | `metadata.intelligence.timings`, `adminDebug`, SSE `activity` | Dentro do alvo do modo (§ 1.4.1) ou shortcut heurístico | Turn analysis/LLM desnecessário; api-delpi lento; RAG pesado |

**Regra de veredito por caso**

| Veredito | Condição |
|----------|----------|
| **PASS** | Todas as dimensões **obrigatórias** da família (tabela § 1.1) em PASS |
| **FAIL** | Qualquer dimensão obrigatória em FAIL |
| **WARN** | Roteamento/tools OK; problema de latência, copy, dado TOTVS zerado, ou paridade não testada |
| **N/A** | Família não aplicável na sessão (ex.: F17 sem host TV) |
| **Inconcluso** | Sem evidência R1–R8 (admin fechado, sem JSON) — re-testar antes de marcar |

**Dimensões obrigatórias por família** (demais = opcional ou N/A)

| Família | Obrigatórias | FAIL imediato se… |
|---------|--------------|-------------------|
| F01 | R1, R2, R4 | Tool ERP no chat comum |
| F02 | R1, R4 | Capabilities desvia para SQL/schedule |
| F03 | R1, R2, R3, R4, R5 | `operationId`/path errado; semantic fallback absurdo |
| F04 | R1, R2, R4 | REST operacional no turno de authoring |
| F05 | R1, R2, R3, R4 | Execute sem agente/action |
| F06–F08 | R1, R2, R4 | Família errada (ERP no web, etc.) |
| F09–F12 | R1, R2, R4 | Ignora anexo/surface (canvas, PDF…) |
| F13 | R1, R5 | Formato/painel incoerente com pedido |
| F14–F15 | R1, R6, R4 | Follow-up/session_review dispara ERP |
| F16 | R1, R2, R4 | Text task vira stock/SQL |
| F17–F18 | R1, R2, R4 | Fora do surface (TV/PAC) |
| F19 | R1, R2, R4 | Clarify em saudação/identidade |
| F20–F21 | R1, R4 | Ignora projeto/glossário |
| F22 | R8 (+ R2 se operacional) | Modo fast com agentic pesado indevido |
| F23 | R4 | Leak de prompt/especialista na bolha |
| F24 | R6, R7 | Simulate diverge de send sem justificativa |

### 1.2 Evidência mínima (colar no ticket ou § 5)

Para cada roteiro, registrar:

```text
ID: F03.1 | Superfície: agente | Veredito: PASS
R1 intentRoute=operational_query | R2 toolCount=1 get_product_stock
R3 code=10080047 | R4 prosa com saldo | R5 table|auto
R6 — | R7 send only | R8 ~2.1s
path=/products/10080047/stock | matchSource=<heuristic|semantic|preflight>
Nota: uma linha se FAIL (módulo canônico suspeito)
```

```text
ID: F03.1 | Superfície: agente | Veredito: PASS
R1 intentRoute=operational_query | R2 toolCount=1 get_product_stock
R3 code=10080047 | R4 prosa com saldo | R5 table|auto
R6 — | R7 send only | R8 totalMs=2100 PASS (alvo normal 5s)
timings: preTool=180 tools=1200 (dominant: wave1HttpMs=980) postTool=40 rag=0 llm=680
path=/products/10080047/stock | matchSource=heuristic | tool.durationMs=980
Nota: uma linha se FAIL (módulo canônico suspeito)
```

Campos admin úteis: `intentRoute`, `tooling.selectedExternalAction.matchSource`, `turnAnalysis.decision`, `skipRag`, `skipTools`, `evidenceRefs`, **`intelligence.timings`**, **`adminDebug.llm.usage.latencyMs`**.

### 1.3 Bateria de interação humana simulada

Além dos gates de domínio (`smoke_chat_flow_families_f01_f04_f03.py`) e da avaliação A–D (`eval_packages_a_d_human_live.py`), existe uma **bateria unificada** que simula usuário real contra a API live (send + `includeAdminDebug`), com os mesmos critérios **R1–R8** deste audit.

**O que simula «humano real»**

| Padrão | Exemplos na bateria | Família |
|--------|---------------------|---------|
| Typos operacionais | `estrutra`, `filail`, `estq` | F03, F01 |
| Abreviações / casual | `o q vc pode fazer`, `ago/26`, `p produzir hj` | F02, F03 |
| PT informal | `me fala … pf`, `qtos tem programado` | F01, F03 |
| Multi-turn na **mesma sessão** | seed estoque → «somente filial 01»; ROL → «mês passado» | F14 |
| Superfície comum × agente | guidance sem agente vs tool com agente | F01, F03 |
| Identity / small talk | `como vc se chama`, `bom dia` | F19 |
| SQL authoring sem leak | `crie sql q liste…` | F04, F23 |

**Script canônico:** `scripts/human_interaction_battery_live.py`

```bash
# Host (gateway local)
cd minha-delpi-ai-api
PYTHONPATH=. .venv/bin/python scripts/human_interaction_battery_live.py

# Container (recomendado em homolog)
docker exec -e SMOKE_BASE_URL=http://delpi-gateway -w /app delpi-minha-delpi-ai-api \\
  python scripts/human_interaction_battery_live.py

# Subconjunto (ex.: regressão tipografia)
SMOKE_ONLY=F03.2-typo-estrutra,F19-B2 python scripts/human_interaction_battery_live.py

# Só famílias
SMOKE_FAMILY=F01,F03,F14 python scripts/human_interaction_battery_live.py
```

**Saída:** `docs/testing/evidence/chat-human-interaction-battery.json` — por caso: `status`, `ms`, `evidence.R1…R8`, `paths`, `operationIds`. Copiar trechos para a planilha § 5.

**Relação com outros harnesses**

| Harness | Escopo | Quando usar |
|---------|--------|-------------|
| `smoke_chat_flow_families_f01_f04_f03.py` | Gates domínio + HTTP mínimo F01/F03/F04 | CI rápido, sem LLM pesado em domain |
| `human_interaction_battery_live.py` | **Bateria F01–F16/F19/F23** + typos + multi-turn | Antes de release inteligência; regressão humana |
| `eval_packages_a_d_human_live.py` | Pacotes A–D (guidance, compare, dataAnswer) | Deep-dive financeiro / compare |
| `smoke_new_intent_user_simulation.py` | SQL execute + new_intent + deixis «isso» | Follow-up SQL / grounding |
| UI manual § 8 | F10, F17, F18, anexos, toolbar apresentação | O que HTTP não cobre |

**Critério de pronto (bateria):** zero `FAIL` nos casos P0 da bateria; `WARN` em R8 documentado com gargalo § 1.4.3; JSON commitado ou anexo ao ticket de release.

**Cadência sugerida**

1. Após mudança em roteamento, turn analysis, selection ou fuzzy lexicon → rodar bateria completa.
2. Após fix pontual → `SMOKE_ONLY=<case_id>` do roteiro afetado.
3. Mensal ou pré-deploy → bateria + amostra manual § 8 (F13 toolbar, F09 anexo).

### 1.4 Latência, alvos e gargalos (R8 — obrigatório registrar)

Toda análise live **mede** tempo e identifica **onde** o turno gastou — não só «demorou». Conteúdo correto com latência fora do alvo = **WARN** em R8 (ou FAIL se família P0 de UX, ex. F19 identity).

#### 1.4.1 Alvos por modo (`response_modes.json` → `latencyTargetsSec`)

| Modo | Alvo `totalMs` (UI) | Interpretação no smoke |
|------|---------------------|-------------------------|
| **Rápida** (`fast`) | ≤ **3 s** | Direct answer / 0–1 tool leve; sem turn analysis LLM |
| **Normal** (`normal`) | ≤ **5 s** | 1 tool REST típica + síntese curta |
| **Pensador** (`thinker`) | ≤ **15 s** | Multi-tool / agentic / RAG aceitável |

**Faixas de veredito R8** (além do alvo do modo):

| Faixa | `totalMs` | Veredito R8 |
|-------|-----------|-------------|
| Dentro do alvo do modo | ≤ alvo | **PASS** |
| Até 2× o alvo | alvo &lt; t ≤ 2× | **WARN** — anotar gargalo |
| &gt; 2× ou &gt;30s em identity/help sem shortcut | — | **FAIL** (bug de rota ou LLM desnecessário) |

Referência histórica: identity sem heurística ~15–45s (`docs/operations/smoke-packages-a-d-human-evaluation.md`) — corrigir em **roteamento pré-LLM**, não «modelo mais rápido».

#### 1.4.2 Onde ler tempos (fontes canônicas)

| Camada | Campo / evento | O que mede |
|--------|----------------|------------|
| **Turno (send)** | `metadata.intelligence.timings` | Spans do pipeline (`ChatPipelineTimings`) |
| **Admin** | `metadata.adminDebug.intelligence.timings` | Mesmo payload compacto |
| **LLM** | `adminDebug.llm.usage.latencyMs` | Só inferência do modelo |
| **Tool HTTP** | `toolCalls[].metadata.durationMs` | Round-trip api-delpi por action |
| **Apresentação** | `toolCalls[].metadata.presentationMs` | Pipeline metadata pós-HTTP |
| **Stream (UX)** | SSE `activity` (`stream.json` → `turnPreparation`) | Percepção: «Procurando…», «Executando…» |
| **Script** | `scripts/smoke_tools_breakdown_stock.py` | Imprime `timings` + maior fatia de `toolsBreakdown` |
| **Eval A–D** | `scripts/eval_packages_a_d_live.py` → `elapsed_ms` | Total por caso automatizado |
| **Bateria humana** | `scripts/human_interaction_battery_live.py` → `evidence.R8` | Total + spans R1–R8 por caso |

Estrutura de `intelligence.timings` (ordem real do prep):

```text
preToolMs   → intent, turn analysis, direct answer, skip flags
toolsMs     → seleção + execução + apresentação das tools
  toolsBreakdown:
    selectionMs (+ selectionBreakdown: native/router/plan/dispatch/embed/db)
    wave1Ms (+ wave1HttpMs, wave1PresentationMs)
    criticMs
    wave2Ms (+ wave2HttpMs, wave2PresentationMs)
    assembleMs | agenticExtendMs | finalizeAfterToolsMs
postToolMs  → pós-tool, enrichment, presentation finalize
ragMs       → retrieve + montagem de contexto documental
llmMs       → síntese final
totalMs     → parede do turno
```

#### 1.4.3 Mapa gargalo → módulo canônico (onde corrigir)

Use a **maior fatia** de `totalMs` (ou de `toolsMs` quando tools dominam) para abrir o ticket no lugar certo:

| Gargalo dominante | Sintoma típico | Módulo canônico (não patch local) |
|-------------------|----------------|-----------------------------------|
| **`preToolMs` alto** + `turnAnalysis` | Identity/help/capabilities ~20–70s; conteúdo ok | `ChatIntentRouter*`, `ChatTurnPreparationTurnAnalysisService`, heurísticas em `identity.json` / `turn_analysis.json` |
| **`selectionMs` / `selectionEmbedMs` / `selectionCandidateDbMs`** | Pausa antes da 1ª tool; muitas actions no agente | `ExternalActionSelection*`, `ExternalActionCandidateDiscoveryService`, cache/embed (`external_action_semantic_*`) |
| **`wave1HttpMs` / `durationMs` na tool** | Uma rota api-delpi lenta | api-delpi (SQL, cache, índice); ver console **Saúde SQL** / `operation_id` |
| **`wave1PresentationMs` / `presentationMs`** | HTTP rápido, turno lento | `ChatPresentationMetadataPipelineService`, perfis JSON, enrichment |
| **`criticMs` / `wave2Ms`** | Segunda onda de tools (enrichment) | `ChatOperationalSufficiencyCriticService`, composition primary/enrichment |
| **`agenticExtendMs`** | Loop agentic extra | `chat_agentic_tool_loop_service`, caps em `tool_context.json` |
| **`ragMs` alto** | Pergunta operacional com retrieve pesado | `ChatTurnPreparationRagService`, skip flags; modo fast não deveria RAG pesado |
| **`llmMs` alto** | Prosa longa após dado já na tool | `ChatTurnCompletion*`, `response_modes` tokens, `ChatPresentationProseDeliveryService` |
| **Stream: gap entre `activity` e 1º token** | UI «travada» sem status | `ChatStreamTurnExecutionService`, textos `stream.json` |

**Regra:** latência por **SQL TOTVS** → api-delpi + cache (`sql-query-development.mdc`); latência por **roteamento/clarify indevido** → chat base (nunca só prompt de agente).

#### 1.4.4 Procedimento por roteiro (checklist R8)

1. Anotar **modo** da sessão (Rápida / Normal / Pensador).
2. Copiar `timings.totalMs` e os 3 maiores spans (`preToolMs`, `toolsMs`, `ragMs`, `llmMs`).
3. Se `toolsMs` &gt; 40% do total → abrir `toolsBreakdown` e registrar o maior (`selectionMs`, `wave1HttpMs`, …).
4. Para cada tool: `path`, `durationMs`, `presentationMs`.
5. Comparar com **alvo § 1.4.1** → PASS/WARN/FAIL R8.
6. FAIL/WARN de latência → ticket com **gargalo + módulo § 1.4.3** (mesmo PR que regressão de conteúdo, se couber).

**Automação de apoio**

```bash
# Breakdown de tools (estoque) — imprime timings e maior span
cd minha-delpi-ai-api
SMOKE_PRODUCT_CODE=10080047 python3 scripts/smoke_tools_breakdown_stock.py

# Pacotes A–D com elapsed_ms por caso
python3 scripts/eval_packages_a_d_live.py
```

#### 1.4.5 Alinhamento mercado (latência)

| Prática mercado | Equivalente DELPI |
|-----------------|-------------------|
| **SLO por modo / percentil** (P50/P95) | `latencyTargetsSec` + faixas WARN/FAIL § 1.4.1 |
| **Trace spans** (OpenTelemetry: router → tool → LLM) | `ChatPipelineTimings` + `toolsBreakdown` |
| **Tool latency separada da síntese** | `durationMs` vs `llmMs` vs `presentationMs` |
| **Eval harness com `elapsed_ms`** | `eval_packages_a_d_live.py`, smoke audit |
| **Não misturar latência com correctness** | R8 separado de R1–R4 (mesma lógica «uma rubrica por dimensão») |

### 1.5 Alinhamento com práticas de mercado (corretude R1–R7)

Os critérios R1–R8 seguem o que plataformas de avaliação de **agentes com tools** tratam como padrão — adaptados ao chat operacional DELPI (api-delpi + apresentação schema-first), não a chat genérico.

| Prática de mercado | Onde aparece | Equivalente DELPI (R1–R8) |
|--------------------|--------------|---------------------------|
| **Tool trajectory / tool-use quality** — ferramenta certa, parâmetros certos, sequência prescrita | [Google ADK — `rubric_based_tool_use_quality_v1`, `multi_turn_tool_use_quality_v1`](https://adk.dev/evaluate/criteria/) | **R2** (trajectory), **R3** (args/slots) |
| **Tool call accuracy** — relevância, parâmetros extraídos da conversa, escala 1–5 | [Azure AI — `ToolCallAccuracyEvaluator`](https://learn.microsoft.com/en-us/python/api/azure-ai-evaluation/azure.ai.evaluation.toolcallaccuracyevaluator) | **R2** + **R3** |
| **Resposta final vs processo** — caminho errado com resposta «ok» ainda é FAIL | ADK: «only one path is considered correct» | **R1** + **R2** antes de **R4** |
| **Uma rubrica por dimensão** — não misturar faithfulness + tools + formato no mesmo julgamento | [Galtea — LLM-as-judge best practices](https://galtea.ai/blog/llm-as-a-judge-prompts-templates-rubrics-and-best-practices) | R1…R8 separados; veredito composto |
| **Trajectory multi-turn** — histórico e follow-up | ADK `multi_turn_*`, frameworks RAG/agent eval | **R6**, **R7** |
| **Faithfulness / grounding** — resposta apoiada em retrieve/tool, não inventada | RAG eval (claim-level), production assistants | **R4** + **R6**; RAG em F07 |
| **Safety / leak** — não expor instruções internas | Critérios safety em ADK; leak guards em prod | Família **F23** → **R4** |
| **Human rubric + automação** — smoke script + julgamento humano com mesma rubrica | ADK yes/no por rubric; eval harnesses | `human_interaction_battery_live.py` + `smoke_chat_flow_families_f01_f04_f03.py` + live § 5 |

**O que não copiamos do mercado (de propósito)**

| Abordagem mercado | Por que fora do smoke live DELPI |
|-------------------|----------------------------------|
| LLM-as-judge em todo caso | Caro, instável; usamos metadata determinística + humano com R1–R8 |
| ROUGE / match textual com referência fixa | Respostas operacionais variam (tabelas, KPI); referência = `operationId` + contrato |
| Score contínuo 1–5 sem critério | Veredito **PASS/FAIL/WARN** por dimensão obrigatória é mais acionável para regressão |

**Referência interna:** avaliação humana A–D (identity, guidance, dataAnswer, compare) — `docs/operations/smoke-packages-a-d-human-evaluation.md` — usa a mesma lógica (causa raiz + evidência metadata, não só bolha).

**Sinais de falha transversais (qualquer família)**

| Sintoma | Suspeita |
|---------|----------|
| Intent certo + tool errada | `semanticFallback` / preflight fraco |
| Intent certo + tool dispara sem pedido | skip tools / authoring gate |
| Eco de «ENTREGA OBRIGATÓRIA», «Modo:», system prompt | leak guard incompleto |
| Resposta de outra família (schedule vs SQL, normas vs cadastro) | conflito de intent |
| Chat comum «consulta» ERP como se tivesse agente | activation / soft-handoff |
| Tabela/KPI no painel sem a pergunta pedir dado | seleção REST indevida |
| `totalMs` &gt; 2× alvo do modo com conteúdo certo | gargalo § 1.4.3 — não é «só UX» |
| `preToolMs` &gt; 5s em identity/help | turn analysis / heurística faltando |
| `wave1HttpMs` domina | api-delpi / SQL / cache |
| `llmMs` domina com tool ok | síntese LLM ou prosa template |

---

## 2. Famílias (mapa)

| ID | Família | Superfície crítica |
|----|---------|-------------------|
| F01 | Ativação de agente | chat comum × agente |
| F02 | Autoajuda / capabilities / fluxos guiados | todos |
| F03 | REST operacional (produto, estoque, KPI, LMP…) | agente |
| F04 | SQL authoring (criar/revisar, sem executar) | agente + skill SQL |
| F05 | SQL execute (`POST /data/sql`) | agente com action |
| F06 | Metadado Protheus (`/system/tables`) | agente |
| F07 | RAG / conhecimento empresa | comum + agente |
| F08 | Pesquisa web | comum + agente |
| F09 | Anexos / OCR / document-vision | comum + agente |
| F10 | Análise de desenhos | agente + skill |
| F11 | Descrição técnica MP / 50xx | skill |
| F12 | Lousa (canvas) | comum + agente |
| F13 | Apresentação (Automático / tabela / gráfico / texto) | agente + MFE |
| F14 | Memória / follow-up / grounding | sessão |
| F15 | Revisão de conversa / busca na sessão | sessão |
| F16 | Textos / e-mail / mixed_task | comum + agente |
| F17 | Copiloto TV Dashboard | host TV |
| F18 | PAC qualidade | agente + skill |
| F19 | Identidade / small talk | comum |
| F20 | Fontes de projeto | projeto |
| F21 | Aprendizagem / glossário | comum |
| F22 | Modos de resposta (Rápida / Normal / Pensador) | UI |
| F23 | Leak / síntese LLM | pós-tool |
| F24 | Simulate / admin debug | admin |

---

## 3. Detalhe por família + roteiros de usuário

Para cada família: **esperado**, **roteiros**, **gaps**, **âncoras**.

### F01 — Ativação de agente

**Esperado:** chat comum **não** executa OpenAPI; guidance +/@ ; agente só com escolha explícita (nunca `default_agent_id` de projeto sozinho).

**Roteiros**

1. (comum) «como ativo o agente?» → instrução +/@; fluxo `agent`; **não** «Consultar produto».
2. (comum) «qual agente consulta produto?» → help agente; **sem** SQL SB1; **sem** schedule.
3. (comum) «qual o estoque do 10080001?» → guidance para ativar agente; sem tool ERP.
4. (agente) «qual o estoque do 10080001?» → tool stock OK.
5. Trocar agente no `+` e perguntar capacidade → só actions daquele agente.

**Gaps / riscos:** soft-handoff vs MFE; exceções (anexo/web/TV) afrouxam skip; catálogo de ajuda stale.

**Âncoras:** `ChatWorkspaceAgentActivationService`, `chatAgentActivation.ts`, `capabilities.json` / `features_catalog` `agent_selection`, `ChatGuidedFlowService`.

---

### F02 — Autoajuda / capabilities / guided flows

**Esperado:** «o que você pode fazer?» lista só o habilitado na sessão; chips não reentram em loops ruins.

**Roteiros**

1. «o que você pode fazer?» (comum vs agente) — comparar cards.
2. «me guie na consulta de estoque» → fluxo `stock`.
3. «como pesquisar na web?» → help web.
4. Chip «Mais opções» / «Como escolher agente?» — não voltar para SQL/produto errado.

**Gaps:** `features_catalog.generation.skillCount` desatualizado vs 7 skills; PAC/TV/desenho pouco descobertos na UX; `pathRules` drift.

**Âncoras:** `ChatCapabilitiesService`, `AssistantCapabilitiesRegistry`, `capabilities.json`, `features_catalog.json`.

---

### F03 — REST operacional

**Esperado:** rota correta por intenção; parâmetros (código/filial/período) pedem clarify se faltarem; **sem** semantic fallback absurdo.

**Roteiros**

1. «estoque do 10080047»
2. «ficha do produto 10080001 em tabela»
3. «ROL de março na filial 01»
4. «LMP da OV …» (número real de teste)
5. «valor total de estoque da empresa» (suprimentos KPI ≠ estoque item)
6. «produtos programados para produzir hoje» (schedule — **só** se pedir programação, não SQL)
7. Sem código: «qual o estoque?» → pedir código / não chutar rota comercial.
8. Follow-up: após produto, «agora os fornecedores».

**Gaps:** `genericSemanticFallback` com `scoreGap: 0`; multi-intent no modo Rápida; chat comum dá falsa esperança.

**Âncoras:** `ExternalActionSelection*`, `operational_route_registry.json`, `api_route_domains.json`, fixtures `SELECTION_CASES` / production operational.

---

### F04 — SQL authoring

**Esperado:** bloco ```sql```; **sem** executar; **sem** REST operacional; sem eco de prompt do especialista.

**Roteiros**

1. «crie um sql que liste os 10 primeiros produtos do grupo 1008»
2. «monte um select de clientes ativos da SA1, sem executar»
3. «explique essa query: SELECT …»
4. «ajuste o sql para trazer os top 10» (após SQL de produtos) → mesma tabela + TOP 10
5. «corrija: SELECT CodigoCliente FROM SA1 …» → colunas Protheus

**Gaps:** UX authoring vs execute pouco clara; `/system` indisponível → sensação de «não fez nada»; leak residual se marcadores faltarem.

**Âncoras:** `ChatSqlAuthoringGuidanceService`, preflight selection, `ChatAdvancedSqlSpecialist*`, `sql_intent_vocabulary.json`.

---

### F05 — SQL execute

**Esperado:** só com action `/data/sql` no agente; confirmação/safety; refinement incremental.

**Roteiros**

1. «execute essa consulta» + SQL no histórico
2. «rode o SQL e traga os 5 produtos do grupo 1008»
3. Chat comum: tentar execute → **não** deve rodar no banco
4. «adicione a coluna cidade e execute de novo»

**Gaps:** skill authoring ON sem action = elabora e não executa (mensagem clara?); show-mode vs execute; templates SQL vs REST.

**Âncoras:** `ChatSqlQueryRefinementService`, SQL fallback policy, `sql_execution_errors.json`.

---

### F06 — Metadado /system

**Roteiros:** «quais colunas da SB1?», «schema da tabela de clientes», «liste tabelas de produto no dicionário».

**Gaps:** ambiguidade com authoring; exige agente + actions `/system`.

---

### F07 — RAG / company-knowledge

**Roteiros:** «o que diz a política de compras?», «explique o glossário de qualidade», «estoque segundo a política» (não deve virar só ERP).

**Gaps:** fast path preserva RAG (custo); colisão com operacional.

---

### F08 — Web search

**Roteiros:** «pesquise na web sobre ISO 9001», «estoque do 10080001 e pesquise na internet sobre o NCM» (misto — API pode ser bloqueada no turno).

**Gaps:** mixed web+ERP; leak na síntese web; flag `web_search_enabled`.

---

### F09 — Anexos / OCR

**Roteiros:** anexar PDF texto «resuma o arquivo»; PDF scan «extraia o texto»; «compare o anexo com o produto 10080001».

**Gaps:** fronteira vision genérica × desenho DELPI; skip tools condicional.

---

### F10 — Desenhos

**Roteiros:** «analise o desenho 90260140», «valide o PDF com o Protheus», «gere relatório de conformidade».

**Gaps:** OCR/unidades; sem skill não deve inventar BOM/SG1; LLM não reclassifica checklist.

---

### F11 — Descrição técnica

**Roteiros:** «como descrever um terminal pino?», «o que significa VDAR?», «explique intermediário 5023…», «me fale do produto 10080001» (deve ser cadastro, **não** normas).

**Gaps:** skill default ON pode interceptar cadastro; preflight bloqueia REST em normas.

---

### F12 — Lousa

**Roteiros:** «coloque isso na lousa», «atualize a lousa com a tabela», «abra o Canva» (não deve virar lousa DELPI).

**Gaps:** `canvas_operational_update` não skip tools; ambiguidade Canva.com.

---

### F13 — Apresentação

**Roteiros:** «em tabela», «gere gráfico», «só texto», «visão integrada/painel»; toolbar Automático vs Texto vs Painel.

**Gaps:** MFE redecidir formato; painel duplicando KPI+tabela; text-first gravando `explicitSessionFormat` indevido (histórico).

**Âncoras:** pipeline presentation delivered puro; `chatPresentation.ts` render-only.

---

### F14 — Memória / follow-up

**Roteiros:** após estoque «somente filial 01»; «e o mês passado?»; «o total não pode ser igual — revise»; «sim» em pending de filial; «isso» / «desse produto».

**Gaps:** meta-conversa vs follow-up; `operationalFocus` não deve forçar operational_query em qualquer msg; proibido `lastEntities`.

---

### F15 — Revisão de sessão

**Roteiros:** «o que me diz sobre a conversa?», «o que eu pedi antes?» → skip tools; não disparar ERP.

---

### F16 — Textos / e-mail

**Roteiros:** «corrija: segue o documento…»; «escreva e-mail formal cobrando prazo»; «consulte estoque do 10080001 e escreva e-mail para compras» (mixed); «corrija: estoque baixo» **não** vira stock.

---

### F17 — TV Dashboard

**Roteiros (no editor TV):** «crie um slide», «escreva um texto neste slide», «pode aplicar». Fora do TV: «monte um slide» ≠ SQL; «monte consulta na tabela SA1» ≠ TV.

**Gaps:** markers fracos (`tabela`+`monte`) ainda em `matches()`; host bypass no chat comum.

---

### F18 — PAC

**Roteiros:** «quais PAC atrasados?», «abrir plano de ação…», write só após «confirmo».

**Gaps:** fora do `features_catalog` / guidedFlows; write confirm.

---

### F19 — Identidade / small talk

**Roteiros:** «quem é você?», «quem sou eu?», «obrigado», «olá» → skip tools; resposta curta.

---

### F20 — Fontes de projeto

**Roteiros:** «o que diz a fonte do projeto?»; «salvar fontes da pesquisa no projeto».

---

### F21 — Aprendizagem / glossário

**Roteiros:** «o que significa LMP?»; fluxo de confirmação de termo.

**Gaps:** pouco coberto em FLOW_FAMILY; colisão com RAG.

---

### F22 — Modos de resposta

**Roteiros:** mesma pergunta operacional em Rápida / Normal / Pensador — comparar tools, RAG, qualidade.

---

### F23 — Leak / síntese

**Roteiros:** após tool, resposta **não** deve citar `humanizedSummary`, `toolCalls`, «according to my instructions», bloco especialista SQL.

**Já mitigado (retest):** echo `[Especialista SQL Avançado]` / ENTREGA OBRIGATÓRIA.

**Gaps:** markers incompletos para drawing/TV/PAC.

---

### F24 — Simulate admin

**Roteiros:** simulate com `previous_messages` de follow-up top N / «agora fornecedores»; sem history não inventar contexto.

**Gaps:** paridade send/stream/simulate.

---

## 4. Skills (catálogo)

Fonte: `app/content/pt-BR/skills/catalog.json` (7 skills).

| Skill | Flag | O que habilita | Gap de descoberta UX |
|-------|------|----------------|----------------------|
| `company-knowledge` | `companyKnowledge` | RAG / KB | OK via feature `rag` |
| `sql` | `sqlAuthoring` (+ derived execute) | Authoring; execute se `/data/sql` | Separação authoring×execute pouco clara |
| `technical-description-delpi` | `technicalDescription` | Normas MP / 50xx | Pode interceptar cadastro |
| `drawing-analysis-delpi` | `drawingAnalysis` | PDF × analyser | Pouco no features_catalog |
| `document-vision-delpi` | `documentVision` | OCR genérico | Fronteira com drawing |
| `quality-action-plans-delpi` | `qualityActionPlans` | PAC | Ausente do catálogo UX |
| `tv-dashboard-copilot` | `tvDashboardCopilot` | Patches TV | Ausente do catálogo UX; surface-only |

**Gap P0 catálogo:** regenerar `features_catalog.json` (`skillCount` legado vs 7 skills) via generator + check CI.

---

## 5. Planilha de teste (preencher no smoke)

**Colunas de critério:** para cada linha, anotar `R1…R8` como `✓` / `✗` / `—` (ver § 1.1). Em **R8**, incluir `totalMs` + span dominante (§ 1.4).

| ID | Roteiro (resumo) | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | Comum | Agente | Veredito | Evidência / nota |
|----|------------------|----|----|----|----|----|----|----|-----|-------|--------|----------|------------------|
| F01.1 | como ativo o agente? | ✓ | ✓ | — | ✓ | — | — | — | ✓ | PASS | — | PASS | domain `flowId=agent`; live `capabilities_catalog`, 0 tools, prosa «Agentes especializados» |
| F01.2 | qual agente consulta produto? | ✓ | ✓ | — | ✓ | — | — | — | ✓ | PASS | — | PASS | não SQL/specialist; live help agente, `selected=None` |
| F01.3 | estoque sem agente | ✓ | ✓ | — | ✓ | — | — | — | ✓ | PASS | — | PASS | domain: `tools_off` + guidance exige agente |
| F03.1 | estoque com código | ✓ | ✓ | ✓ | ✓ | ✓ | — | — | ✓ | — | PASS | PASS | domain stock-action; live `path=/products/10080001/stock` |
| F03.6 | programação hoje (REST ok) | ✓ | ✓ | ✓ | ✓ | — | — | — | ✓ | — | PASS | PASS | domain selection `get_production_schedule_today` |
| F04.1 | crie sql grupo 1008 | ✓ | ✓ | — | ✓ | — | — | — | ✓ | — | PASS | PASS | preflight `selected=None`; live SQL sem schedule/leak (`sub=no_rag`) |
| F04.4 | ajuste top 10 | ✓ | ✓ | ✓ | ✓ | — | ✓ | — | ✓ | — | PASS | PASS | domain normalize: SB1 + TOP 10, sem A1 |
| F04.leak | strip ENTREGA OBRIGATÓRIA | — | — | — | ✓ | — | — | — | — | — | PASS | PASS | domain prose formatting |
| F05.1 | execute SQL | | | | | | | | | | | | |
| F07.1 | política compras RAG | | | | | | | | | | | | |
| F08.1 | pesquise na web | | | | | | | | | | | | |
| F10.1 | analise desenho | | | | | | | | | | | | |
| F11.1 | normas vs cadastro | | | | | | | | | | | | |
| F13.1 | em gráfico / tabela | | | | | | | | | | | | |
| F14.1 | follow-up filial | | | | | | | | | | | | |
| F16.1 | mixed estoque+email | | | | | | | | | | | | |
| F17.1 | crie slide (host TV) | | | | | | | | | | | | |
| F18.1 | PAC atrasados | | | | | | | | | | | | |
| F23.1 | leak pós-tool | | | | | | | | | | | | |

*(Smoke automatizado: `docker exec -e SMOKE_BASE_URL=http://delpi-gateway -w /app delpi-minha-delpi-ai-api python scripts/smoke_chat_flow_families_f01_f04_f03.py`.)*

*(Bateria interação humana: `docker exec -e SMOKE_BASE_URL=http://delpi-gateway -w /app delpi-minha-delpi-ai-api python scripts/human_interaction_battery_live.py` → JSON em `docs/testing/evidence/chat-human-interaction-battery.json`.)*

---

## 6. Prioridade de caça a bugs (próxima onda)

| Pri | Tema | Por quê |
|-----|------|---------|
| P0 | Gate selection por `subIntent` do router (não só authoring SQL) | Intent certo + tool errada ainda possível fora do SQL |
| P0 | Regenerar `features_catalog` + descoberta PAC/TV/drawing | UX e help mentem sobre capacidades |
| P0 | FLOW_FAMILY + live: drawing, PAC, TV, SQL execute, presentation, mixed | Matriz de gates incompleta |
| P0 | Simulate com `previous_messages` | Follow-up quebrado em admin |
| P1 | Conflitos: tech-description × produto; web × ERP; session × focus | Falsos positivos |
| P1 | Soft-handoff chat comum alinhado ao MFE | «consulta» sem agente |
| P1 | SQL authoring vs execute na ajuda | Expectativa do usuário |
| P2 | Learning/glossário em fixtures | Cobertura baixa |
| P2 | Leak markers drawing/TV/PAC | Família F23 |

---

## 7. Mapa de artefatos relacionados

| Papel | Path |
|-------|------|
| **Este documento (canônico)** | `docs/testing/chat-ai-flow-families.md` |
| Índice de testes | `docs/testing/README.md` |
| Bateria HTTP (typos, multi-turn) | `scripts/human_interaction_battery_live.py` |
| Gates domínio F01/F03/F04 | `scripts/smoke_chat_flow_families_f01_f04_f03.py` |
| Eval A–D (compare, dataAnswer) | `scripts/eval_packages_a_d_human_live.py` |
| SQL / new_intent / deixis | `scripts/smoke_new_intent_user_simulation.py` |
| Saída JSON da bateria | `docs/testing/evidence/chat-human-interaction-battery.json` |
| Eval A–D (histórico) | `docs/operations/smoke-packages-a-d-human-evaluation.md` |
| Perguntas copy-paste manual | `docs/testing/perguntas-teste-chat-jun2026.md` |

### 7.1 Referências técnicas

| Artefato | Path |
|----------|------|
| Inteligência base | `docs/architecture/chat-intelligence-base.md` |
| Skills | `app/content/pt-BR/skills/catalog.json`, `docs/api/11-skills.md` |
| Features UX | `app/content/pt-BR/assistant/features_catalog.json` |
| Capabilities / guided | `app/content/pt-BR/assistant/capabilities.json` |
| Intent router content | `app/content/pt-BR/assistant/intent_router.json` |
| Fixtures intent | `tests/fixtures/intent_router_regression_cases.py` |
| Fixtures intelligence | `tests/fixtures/chat_intelligence_regression_cases.py` |
| Matriz famílias (gates) | `tests/unit/domain/services/test_flow_family_matrix_gates.py` |
| Critérios smoke live (R1–R8) | **este doc § 1.1–1.5** |
| Latência / gargalos (`ChatPipelineTimings`) | **este doc § 1.4**; `app/application/services/chat_pipeline_timings.py` |
| Smoke breakdown estoque | `scripts/smoke_tools_breakdown_stock.py` |
| Skip tools | `chat_turn_preparation_tool_routing_service.py` |
| Preflight selection | `external_action_selection_preflight_service.py` |
| MFE ativação | `plugins/minha-delpi-chat/src/state/chatAgentActivation.ts` |

---

## 8. Protocolo sugerido de sessão de teste

### 8.1 Automação (HTTP — interação humana simulada)

1. Stack live via gateway (`SMOKE_BASE_URL=http://delpi-gateway` no container).
2. Rodar **`human_interaction_battery_live.py`** (bateria completa) ou filtro `SMOKE_FAMILY` / `SMOKE_ONLY`.
3. Revisar resumo no terminal + `docs/testing/evidence/chat-human-interaction-battery.json`.
4. Para cada `FAIL`: copiar `evidence` do caso para ticket (§ 1.2) + módulo canônico § 1.4.3.
5. Complementar com `eval_packages_a_d_human_live.py` (compare/dataAnswer) e `smoke_new_intent_user_simulation.py` (SQL execute / deixis).

### 8.2 Manual (UI — o que a bateria não cobre)

1. Sessão **nova** (sem histórico contaminado).
2. Diagnóstico admin aberto (intent / tools / RAG).
3. Para **cada roteiro**: preencher **R1–R8** (§ 1.1) + **timings** (§ 1.4) → veredito → evidência (§ 1.2).
4. Ordem sugerida: **F01 → F04 → F03 → F14 → F13 → F08 → F16 → F10 → F17 → F18**.
5. Para cada FAIL: salvar JSON de diagnóstico (`intentRoute`, `tooling.selectedExternalAction.matchSource`, `evidenceRefs`) neste doc ou ticket + módulo canônico suspeito.
6. Só então corrigir no módulo canônico + teste de regressão da família.
