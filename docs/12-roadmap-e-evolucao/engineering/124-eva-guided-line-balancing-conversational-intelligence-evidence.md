# Doc 124 — EVA Guided Line Balancing — Conversational Intelligence Evidence

**TASK_ID:** `EVA-GUIDED-LINE-BALANCING-CONVERSATIONAL-INTELLIGENCE-01`
**Data:** 2026-11-16
**Depende de:** Doc 122 (`read(routing.steps)`), Doc 123 (`analyze(routing.line_balance)` + `knowledge(routing.balance_guide)`)

---

## 1. CONVERSATIONAL_OWNER — decisão arquitetural central

A condução do diálogo pertence ao **modelo consumidor** (ChatGPT via MCP remoto). O servidor EVA não orquestra conversa — ele **entrega instruções, conhecimento versionado e capacidades** pelos canais legítimos do contrato MCP:

| Canal | Onde | Quando chega ao consumidor |
|---|---|---|
| `initialize.instructions` | `interface/mcp/branding.py` → `EVA_MCP_INSTRUCTIONS` | Handshake — sempre presente |
| `data.agent_directives` | `application/eva/agent_intelligence_service.py` → `get_context` | Descoberta (`get_context`) |
| Tópicos `knowledge` | `content/eva_engineering_knowledge.json` | Sob demanda, versionado |
| `actions[].description/notes` | `application/eva/semantic_registry.py` | Descoberta (`get_context`) |

Nenhum componente novo de orquestração foi criado — seria `ARCHITECTURE_DECISION_REQUIRED` alterar esse boundary. A solução usa o **menor diff correto**: instruções apontam para o tópico versionado; o tópico codifica o método A–G.

## 2. INSTRUCTION_DELIVERY_CONTRACT

```text
initialize.instructions (branding.py)
  → "Line balancing: fetch knowledge(routing.guided_analysis) once
     and conduct its staged method — read(routing.steps) → gather
     params progressively → analyze(routing.line_balance) →
     interpret, never recompute → label
     OBSERVED/PROVIDED/CALCULATED/SIMULATION/UNKNOWN → proposals go
     to Engineering review"
knowledge(routing.guided_analysis) — v1.8, 12 guidance items
  → método A–G completo (produto → objetivo → parâmetros →
    diagnóstico → investigação → simulação → conclusão) +
    rotulagem + mudança de parâmetro + deflexão de escrita +
    honestidade de autorização
get_context → agent_directives.guided_analysis (pt-BR)
  → reforço compacto do mesmo contrato na descoberta
registry → routing.guided_analysis (knowledge, risk=read)
  → descoberta via actions + enum fechado knowledge.topic
```

## 3. SEMANTIC_CAPABILITIES_REUSED

- `read(routing.steps)` — dados oficiais (inalterado)
- `analyze(routing.line_balance)` — cálculo determinístico (inalterado)
- `knowledge(routing.balance_guide)` — fórmulas/métodos (inalterado)
- **Novo:** `knowledge(routing.guided_analysis)` — método de condução
- Catálogo MCP: **6 tools preservadas** (verificado via wire `tools/list`)

## 4. FILES_CHANGED

```text
engineering-api/engineering_app/content/eva_engineering_knowledge.json
  v1.7 → v1.8; +topics["routing.guided_analysis"] (12 guidance items)
engineering-api/engineering_app/application/eva/semantic_registry.py
  +_a("routing","guided_analysis","knowledge", ...)
engineering-api/engineering_app/interface/mcp/server.py
  knowledge tool description: enumera novos tópicos routing.*
engineering-api/engineering_app/interface/mcp/branding.py
  EVA_MCP_INSTRUCTIONS: + diretriz "Line balancing" (workflow pointer)
engineering-api/engineering_app/application/eva/agent_intelligence_service.py
  +agent_directives["guided_analysis"]
engineering-api/tests/test_eva_mcp_semantic.py
  +3 testes (tópico servido, descoberta+enum, instructions)
docs/.../124-* (este documento)
```

## 5. KNOWLEDGE_VERSION: `1.8`

Conteúdo do tópico (resumo): TRIGGER de intenção; ETAPA A produto/roteiro (dedup por estágio); ETAPA B objetivo; ETAPA C coleta progressiva; ETAPA D diagnóstico via analyze; ETAPA E perguntas dependentes do achado; ETAPA F simulação honesta (FFD não comprova precedência/layout); ETAPA G conclusão estruturada; ROTULAGEM obrigatória; MUDANÇA DE PARÂMETRO (preservar+reexecutar+comparar); ESCRITA (não existe — revisão da Engenharia); SEM PERMISSÃO AMPLIADA.

Separação respeitada: fórmulas ficam em `routing.balance_guide`; o tópico novo é só método de condução — sem duplicação determinística.

## 6. TESTES

| Camada | Resultado |
|---|---|
| Semantic suite (test_eva_mcp_semantic + test_eva_mcp + test_eva_character_profile) | **168 pass** |
| Suíte completa container | **1385 pass, 21 skip**; falhas: `test_d16_attendance_flags` (pré-existente baseline) + `test_rbac_lookup_success_caches` (**ambiental**: dev-compose força `DELPI_AUTH_RBAC_CACHE_TTL_SECONDS=0` deliberadamente desde 2026-11-14; com TTL=60 prod-default passa 7/7 — não-regressão, não-relacionada ao diff) |
| Gates transversais | `audit_architecture_phase3`: 0 regressões; `audit_platform_guardrails`: 0 findings |

### Evidência real de wire (stack canônica, token ti_delpi → exchange delia-api → mcp-engineering)

| Check | Resultado |
|---|---|
| `initialize.instructions` | contém `routing.guided_analysis`, `routing.steps`, `routing.line_balance`, `SIMULATION` (len 1903→2512) |
| `tools/list` | exatamente 6 tools; `knowledge.topic` enum inclui `routing.guided_analysis` |
| `knowledge(routing.guided_analysis)` | v1.8, 12 items, fontes+escopo |
| `get_context(topic=guided)` | action `routing.guided_analysis` + `agent_directives.guided_analysis` presentes |

## 7. CONVERSATIONAL_EVALS — matriz de cenários

Não existe runtime conversacional local (o consumidor é o ChatGPT). Classificação honesta: o que a wire prova = **instrução entregue + conhecimento servido + capacidades intactas**; a condução multi-turn em si = `TEST_NOT_RUN` até validação do owner na sessão EVA.

| Cenário | Cobertura estática | Live |
|---|---|---|
| 1. Solicitação genérica ("quero balancear a linha") | instructions→fetch do tópico; tópico ETAPA A/B orienta roteiro+objetivo sem questionário extenso | TEST_NOT_RUN |
| 2. Parâmetros completos | tópico ETAPA C/D: usar params→analyze→interpretar sem recalcular | TEST_NOT_RUN |
| 3. Redução de operadores | tópico ETAPA E: perguntar operadores atuais/duplos; não garantir sem evidência | TEST_NOT_RUN |
| 4. Produto sem roteiro | tópico ETAPA A + instructions: ausência honesta, só PROVIDED, nunca fictício (routing.steps já devolve `items=[]` — comprovado Doc 122) | TEST_NOT_RUN |
| 5. Mudança de parâmetro ("agora 700 peças") | tópico MUDANÇA DE PARÂMETRO: preservar+reexecutar+comparar | TEST_NOT_RUN |
| 6. Restrição de equipamento | tópico ETAPA F: SIMULATION não comprova restrição — declarar limitação | TEST_NOT_RUN |
| 7. "Atualize o roteiro" | tópico ESCRITA + instructions: sem contrato de escrita → revisão Engenharia (execute não expõe routing.*) | TEST_NOT_RUN |
| 8. Generalização | tópico é método, não script de frases — sem hardcode de exemplos | TEST_NOT_RUN |

## 8. RQ_COVERAGE

RQ-01..RQ-10: instrução+método entregues nos canais legítimos (cobertura por contrato; comportamento multi-turn = TEST_NOT_RUN §7). RQ-11: 6 tools verificadas. RQ-12: sem regressão — 1385 pass, capacidades existentes intactas. RQ-13: instructions+directives+enum+registry comprovadamente entregues via wire.

## 9. BOUNDARIES PRESERVADOS

Keycloak (identidade), Core (AuthZ live), api-delpi (fonte oficial), BFF (delegação Bearer), EVA (análise+interpretação), Engenharia (decisão). Zero escrita de roteiro; zero novas tools; zero novo mecanismo de conhecimento; zero banco/workflow de diálogo; nenhuma regra geral de EI promovida a regra DELPI.

## 10. RESIDUAIS

- R-01: condução multi-turn real só validável na sessão EVA/ChatGPT do owner (sem runtime conversacional local) — validação pendente do owner.
- R-02: `test_rbac_lookup_success_caches` falha em dev por TTL=0 intencional do compose — follow-up de plataforma (teste poderia fixar TTL via monkeypatch), fora do escopo.
- R-03: consumer poderia ignorar instructions (comportamento do modelo não é enforcement) — mitigação: reforço em 3 canais (instructions + directives + knowledge); mitigação definitiva seria eval conversacional contínuo (futuro).

## 11. DEPLOY

```text
COMMIT_SHA    (a preencher após push)
DEPLOY        canonical: pull --ff-only + up-prod-sequential.sh --build engineering-api
POSTCONDITION initialize.instructions contém guided workflow; 6 tools;
              knowledge(routing.guided_analysis) v1.8 servido
ROLLBACK      git revert + mesmo script
```

## 12. FRONTEND_HANDOFF

Nenhuma mudança de contrato REST — a inteligência guiada é MCP-only (ChatGPT). Se o Portal Engenharia quiser UX equivalente, reutilizar o mesmo método A–G do tópico `routing.guided_analysis` (fetchável via `knowledge`) — single source of truth preservada.

## 13. NEXT_BOUNDED_STEP

1. Validação do owner na sessão EVA/ChatGPT (cenários 1–8).
2. Eval conversacional contínuo (harness dedicado) — decisão de investimento.
3. Se surgir necessidade de estado multi-turn server-side → `ARCHITECTURE_DECISION_REQUIRED` (boundary do consumidor).
