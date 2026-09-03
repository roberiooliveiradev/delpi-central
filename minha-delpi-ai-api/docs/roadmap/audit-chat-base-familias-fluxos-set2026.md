# Auditoria — famílias do chat base, agentes e skills (set/2026)

**Objetivo:** inventário acionável para caçar bugs/gaps por família, com **roteiros de usuário** (PT-BR) prontos para smoke live depois.  
**Escopo:** chat base (`minha-delpi-ai-api`) + MFE `plugins/minha-delpi-chat` + skills/agentes.  
**Princípio:** inteligência transversal no chat base; agentes só filtram actions/skills/prompt (`docs/architecture/chat-intelligence-base.md`).

**Status deste doc**

| Item | Estado |
|------|--------|
| Inventário + roteiros | ✅ pronto |
| Unitários das regressões recentes (agente / SQL authoring / leak) | ✅ verdes (set/2026) |
| Smoke domain + HTTP F01 / F04 / F03 | ✅ **18/18 PASS** (set/2026) — `scripts/smoke_audit_familias_f01_f04_f03.py` |
| Smoke live UI (demais famílias § 5) | ⏳ pendente |

**Mitigações recentes (já no código — revalidar no live):**

- Help/ativação de agente ≠ fluxo produto; «consulta» solta ≠ SQL.
- Authoring SQL (`crie/monte SQL`) **bloqueia** REST operacional (ex.: programação).
- Follow-up top N não troca família Protheus (SB↔SA).
- Strip de leak do especialista SQL + marcadores em `llm_synthesis_delivery.json`.
- TV: `monte+tabela` não sequestra SQL fora do surface.

---

## 1. Como usar este audit

1. Escolher uma **família** (Fxx).
2. Rodar os **roteiros** em: chat comum → agente Minha DELPI → (se couber) projeto / simulate admin.
3. Marcar na tabela § 5: `PASS` / `FAIL` / `N/A` + evidência (operationId, intentRoute, screenshot).
4. FAIL → causa raiz no **módulo canônico** da família (não patch no MFE/agente).

**Sinais de falha transversais (qualquer família)**

| Sintoma | Suspeita |
|---------|----------|
| Intent certo + tool errada | `semanticFallback` / preflight fraco |
| Intent certo + tool dispara sem pedido | skip tools / authoring gate |
| Eco de «ENTREGA OBRIGATÓRIA», «Modo:», system prompt | leak guard incompleto |
| Resposta de outra família (schedule vs SQL, normas vs cadastro) | conflito de intent |
| Chat comum «consulta» ERP como se tivesse agente | activation / soft-handoff |
| Tabela/KPI no painel sem a pergunta pedir dado | seleção REST indevida |

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

| ID | Roteiro (resumo) | Comum | Agente | Projeto | Simulate | Evidência / nota |
|----|------------------|-------|--------|---------|----------|------------------|
| F01.1 | como ativo o agente? | PASS | — | — | — | domain `flowId=agent`; live `capabilities_catalog`, 0 tools, prosa «Agentes especializados» |
| F01.2 | qual agente consulta produto? | PASS | — | — | — | não SQL/specialist; live help agente, `selected=None` |
| F01.3 | estoque sem agente | PASS | — | — | — | domain: `tools_off` + guidance exige agente |
| F03.1 | estoque com código | — | PASS | — | — | domain stock-action; live `path=/products/10080001/stock` |
| F03.6 | programação hoje (REST ok) | — | PASS | — | — | domain selection `get_production_schedule_today` |
| F04.1 | crie sql grupo 1008 | — | PASS | — | — | preflight `selected=None`; live SQL sem schedule/leak (`sub=no_rag`) |
| F04.4 | ajuste top 10 | — | PASS | — | — | domain normalize: SB1 + TOP 10, sem A1 |
| F04.leak | strip ENTREGA OBRIGATÓRIA | — | PASS | — | — | domain prose formatting |
| F05.1 | execute SQL | | | | | |
| F07.1 | política compras RAG | | | | | |
| F08.1 | pesquise na web | | | | | |
| F10.1 | analise desenho | | | | | |
| F11.1 | normas vs cadastro | | | | | |
| F13.1 | em gráfico / tabela | | | | | |
| F14.1 | follow-up filial | | | | | |
| F16.1 | mixed estoque+email | | | | | |
| F17.1 | crie slide (host TV) | | | | | |
| F18.1 | PAC atrasados | | | | | |
| F23.1 | leak pós-tool | | | | | |

*(Smoke automatizado: `docker exec -e SMOKE_BASE_URL=http://delpi-gateway -w /app delpi-minha-delpi-ai-api python scripts/smoke_audit_familias_f01_f04_f03.py`.)*

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

## 7. Referências rápidas

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
| Skip tools | `chat_turn_preparation_tool_routing_service.py` |
| Preflight selection | `external_action_selection_preflight_service.py` |
| MFE ativação | `plugins/minha-delpi-chat/src/state/chatAgentActivation.ts` |

---

## 8. Protocolo sugerido de sessão de teste

1. Sessão **nova** (sem histórico contaminado).
2. Diagnóstico admin aberto (intent / tools / RAG).
3. Ordem sugerida: **F01 → F04 → F03 → F14 → F13 → F08 → F16 → F10 → F17 → F18**.
4. Para cada FAIL: salvar JSON de diagnóstico (`intentRoute`, `tooling.selectedExternalAction.matchSource`, `evidenceRefs`) neste doc ou ticket.
5. Só então corrigir no módulo canônico + teste de regressão da família.
