# DÉLIA — Roadmap bounded · Inteligência contextual MCP e organização do orquestrador

**DATA:** 2026-10-19 (roadmap state refresh; original baseline remains historical)
**TRACK_ID:** `DELIA-C3-MCP-CONTEXTUAL-INTELLIGENCE-AND-ORCHESTRATOR-QUALITY-01`
**STATUS:** `I00_ACCEPTED_WITH_RESIDUAL / I01_ACCEPTED_WITH_RESIDUAL / I02_ACCEPTED_WITH_RESIDUAL_SCOPED / I03_ACCEPTED_WITH_RESIDUAL / I04_EVIDENCE_READY / Q01–Q03_PLANNED`
**Baseline HEAD:** `cc7d2c8e3ba0d70edd56088df72ee795976c2e2e` (revalidar em cada execução).
**Origin evidence:** [44](../conversational-intelligence-c3/44-specialist-knowledge-utilization-eval.md); I01 [03](./03-i01-contextual-knowledge-continuity-implementation.md)/[04](./04-i01-independent-architecture-acceptance.md); I02 [05](./05-i02-grounded-knowledge-synthesis-implementation.md), ledger §6.243.

## 1. Decisão de produto e escopo

**Primeiro a inteligência funcional, depois a organização do código.** DÉLIA deve utilizar profundamente as capabilities e o conhecimento **vivo** de DAVI, TÉO, VISTA e novos providers, dentro do contexto da conversa/trabalho ativo; **não** incorporar ou duplicar globalmente a base do especialista, nem transformá-la em autoridade/memória persistente. Uso abrangente significa todas as **capabilities autorizadas e relevantes**, não invocar todas a cada turno nem promover automaticamente ACT.

`SPECIALIST_KNOWLEDGE_OWNER=SPECIALIST`; `DELIA_SPECIALIZATION=DYNAMIC_CONTEXTUAL_PROVIDER_NEUTRAL`; `GLOBAL_MCP_KNOWLEDGE_COPY=NO`; `UNREVIEWED_ORGANIZATIONAL_KNOWLEDGE_PUBLISH=NO`. Retenção da conversa (produto) e retenção de evidência operacional são preocupações distintas; nenhuma nova persistência é autorizada aqui.

**Observado, não extrapolado:** K1 TÉO `PASS_WITH_LIMITATION`, K2 TÉO `FAIL` (reconsulta, replay literal, 30,014ms), K3 VISTA `PASS_WITH_LIMITATION` (guia bruto/truncado), K4 DAVI `PASS_WITH_LIMITATION` (discovery empty-match); `KNOWLEDGE_DISCOVERY=PASS`, `KNOWLEDGE_UTILIZATION=PARTIAL`, `KNOWLEDGE_TO_NEXT_STEP=FAIL`. READ-only, material ACT=0. Esta amostra **não** prova que DÉLIA nunca utiliza conhecimento dos MCPs.

## 2. Autoridades e invariantes

Em **toda** tarefa: HEAD + git status e regras do projeto/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → spec temática → ledger → código/evidência SHA. Divergência com fonte superior: STOP / `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`; não reconciliar silenciosamente.

**Reuse-first:** antes de novo port/adapter/service/context/registry/engine, provar `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY` e `REUSE_DECISION=REUSE|EXTEND|NEW`. Existing: `OperationalCapabilityOrchestrator`, `ConversationContextTurn`, `_understand_goal`, `_prior_continuation_attempt`, `_synthesize_content`, `_resolve_missing_inputs`, provider surfaces, owner evidence/provenance e deadlines. Conferir implementação no HEAD.

Keycloak identidade; Core live AuthZ; Domain API autoridade factual/regras; owner MCP detém catálogo e guidance; DÉLIA orquestra seleção/Policy/Decision/Evidence; MCP output, guidance, metadata e contexto anterior são **untrusted**, jamais AuthZ, FACT novo, Policy ou instruções do sistema. `DISCOVERY != APPROVAL`; `GUIDANCE != DOMAIN_FACT`; `READ != PREPARE != ACT`; `MESSAGE != ACT`; `MODEL_AUTHORED_FACTUAL_PROSE=NONE`. `GLOBAL_TURN_BUDGET_SECONDS=30`; nenhuma ampliação de timeout. Não criar branch de especialista no planner, cópia do catálogo ou engine paralelo.

**I00 formalmente aceita:** [01 — independent context baseline acceptance](./01-i00-independent-context-baseline-acceptance.md). A revisão prova o fluxo de contexto transitório e limitações do contrato examinado; não prova causa raiz do K2 nem autoriza I01 automaticamente.

**I01 direction proposed:** [02 — architecture alignment and continuity proposal](./02-i01-architecture-alignment-and-continuity-proposal.md).
**I01 implementation candidate (not independently accepted):** [03 — contextual knowledge continuity implementation](./03-i01-contextual-knowledge-continuity-implementation.md). `EXISTING_EQUIVALENT=YES` / `REUSE_DECISION=EXTEND`; live K2 path sem reconsulta desnecessária; `I01_ACCEPTED=NO` até review.

**I01 independente:** [04 — architecture acceptance](./04-i01-independent-architecture-acceptance.md) = ACCEPT_WITH_RESIDUAL.
**I02 implementation candidate:** [05 — grounded knowledge synthesis](./05-i02-grounded-knowledge-synthesis-implementation.md). Deterministic guidance projection + budget-safe fallback; `I02_ACCEPTED=YES_WITH_RESIDUAL` até review.

**I02 independent review:** [06 — REWORK decision](./06-i02-independent-review-rework-decision.md).
**I02-R1 diagnosis:** [07 — post-fix validation and latency diagnosis](./07-i02r1-post-fix-validation-and-latency-diagnosis.md) — nested live INCONCLUSIVE (index_probe timeout before READ); pre-synthesis latency PROVEN (`index_probe` model under 30s). Performance fix not applied.

**I02-R1 independent diagnostic acceptance:** [08 — acceptance with safety qualification](./08-i02r1-independent-diagnostic-acceptance.md). K3 index_probe pre-owner latency PROVEN; nested fix not exercised. I02-R2 must bound optional probe **before** model call; never continue after global deadline expiry or present an empty/index READ as full answer.

**I02-R2 implementation candidate:** [09 — index probe headroom fix and deploy](./09-i02r2-index-probe-headroom-fix-and-deploy.md). Owner-contract PT + derived headroom; live K3 GROUNDED com INDEX/READ/nested sem model probe; K1/K2 TEO ainda timeout. `I02_ACCEPTED=NO` até review.

**I02-R2 independent review:** [10 — bounded fix accepted with residuals](./10-i02r2-independent-architecture-and-deploy-review.md). I02 remains REWORK because K1/K2 live FAIL; optional probe floor and PT contract heuristic have open generalization risk. Next: I02-R3 pre-owner TÉO latency diagnosis and design.

**I02-R3 (coordenação, investigação parcial):** [11 — latency architecture investigation](./11-i02r3-coordination-latency-architecture-investigation.md). Confirmado: várias propostas do modelo antes do owner, sem prova ainda de quais podem ser eliminadas; nenhuma solução de código aprovada. Próximo gate = perfis de K1 PASS/FAIL e dependências entre estágios antes do prompt de implementação.

**I02-R3 — task do consultor (análise/testes, sem implementação):** [12 — consultant diagnostic task](./12-i02r3-consultant-diagnostic-task.md). O consultor comprova etapa exata de timeout K1, mapa de dependências, suíte de caracterização e alternativas A–F; decisão de arquitetura e eventual patch ficam com a coordenação.

**I02-R3 — evidência do consultor:** [13 — evidence and dependency analysis](./13-i02r3-consultant-evidence-and-dependency-analysis.md). Timeout K1 **PROVEN** em `arguments` pós-`get_catalog`; K3 R2 regressão OK; recomendação F+headroom arguments; **sem** patch funcional nem deploy.

**I02-R3 — decisão independente:** [14 — diagnostic review and architecture decision](./14-i02r3-independent-diagnostic-review-and-architecture-decision.md). Diagnosis ACCEPT_WITH_RESIDUAL; R3-A budget experiment then R3-B critical-path gate; stage-cap 10s **not** production-approved.

**I02-R3 independent review + architecture direction:** [14 — diagnosis accepted, staged budget experiment and critical-path gate](./14-i02r3-independent-diagnostic-review-and-architecture-decision.md). K1 `arguments` timeout PROVEN; arbitrary 10s global stage cap NOT approved as functional fix. I02 remains REWORK.

**I02-R3A — experimentos controlados:** [15 — budget and critical-path experiments](./15-i02r3a-controlled-budget-and-critical-path-experiments.md). E0–E5 sintéticos: cap 10 antecipa falha; headroom opt-in só honest skip; E3–E5 sem merge/bypass default; produção inalterada.

**I02-R3A independent review:** [16 — experiment evidence accepted with residuals](./16-i02r3a-independent-experiment-review.md). No K1 task-success improvement demonstrated, stage cap 10s not approved in production, arguments guard OFF. Next R3-B typed-selection contract/safety experiment gate; no functional merge approved.

**I02-R3B — typed capability+goal (cold-start):** [17 — implementation evidence](./17-i02r3b-typed-capability-goal-selection-implementation.md). Cold-start consolidates capability+goal in one typed propose (−1 model call when `goal_class` present); legacy/incomplete payloads fall back to dedicated `turn_goal`. Native skip / stage-cap / arguments-headroom defaults unchanged. Live K1 `TEST_NOT_RUN`. `I02_ACCEPTED=NO` until independent review.

**I02-R3B independent implementation review:** [18 — typed routing accepted with residuals, live outcome pending](./18-i02r3b-independent-implementation-review.md). Cold-start eligible path avoids one model proposal in synthetic tests; K1/K2/K3 authenticated live not yet run. I02 remains REWORK.

**I02-R3B authenticated live outcome:** [19 — live K1/K2/K3 validation](./19-i02r3b-authenticated-live-outcome-validation.md). Runtime already contained R3-B; K1 TEO methodology READ in 21469ms with typed merge (no separate `turn_goal`); K2 continuity without owner reinvoke; K3 VISTA INDEX→topic→guidance. `I02_ACCEPTED=NO` until coordination review.

**I02-R3B live validated:** [19 — authenticated K1/K2/K3](./19-i02r3b-authenticated-live-outcome-validation.md), independently reviewed in [20 — ACCEPT_WITH_RESIDUAL](./20-i02r3b-independent-live-outcome-review.md). K1 TÉO methodology READ in 21.469s; K2 output short (48 chars), K3 topic relevance partial. No causal A/B or p95; I02 still REWORK.

**Adaptive routing completion (candidate):** [21 — implementation + live](./21-adaptive-capability-routing-completion-implementation.md). Extends `OperationalCapabilityOrchestrator` (no second planner): safe FAST telemetry, comparison-declared native skip, deterministic eligible args, K2 thin-extraction expand + K3 index ranking. Full pytest PASS; live SHA `c2ae80e364` K1 20.2s TEO READ, K2 130 chars (was 48), K3 INDEX→`display_formats`. `ALGORITHM_COMPLETION=PARTIAL`; `I02_ACCEPTED=NO`.

**Adaptive routing completion:** [21 — implemented slices and live evaluation](./21-adaptive-capability-routing-completion-implementation.md); [22 — independent ACCEPT_WITH_RESIDUAL review](./22-adaptive-capability-routing-independent-review.md). FAST telemetry only; OPERATIONAL functional; K2 usefulness and K3 topic relevance residuals; algorithm PARTIAL, I02 not accepted.

**I02 K2/K3 next bounded implementation:** [23 — execution brief](./23-i02-k2-k3-quality-remediation-execution-brief.md). This is a task brief, not implementation or phase acceptance. K1 live pass with truncation preserved; K2 usefulness and K3 semantic topic relevance remain open.

**I02 K2/K3 quality remediation (candidate):** [24 — implementation + live](./24-i02-k2-k3-output-quality-remediation-implementation.md). Coverage-based prior extraction; index relevance floor + weak-topic reject. Live SHA `ddf0bef787`: K1 TEO 17.0s; K2 checklist 219 chars / 5 bullets / no reinvoke; K3 INDEX→`no_match`→clarification (not `display_formats`). `I02_ACCEPTED=NO`.

**I02 K2/K3 remediation:** [24 — implementation and live evidence](./24-i02-k2-k3-output-quality-remediation-implementation.md), [25 — independent ACCEPT_WITH_RESIDUAL review](./25-i02-k2-k3-independent-remediation-review.md). K1=17.010s TÉO READ; K2=5 bullets/219 chars; K3 safe no-match clarification near 30s, not nested topic success. Next: I02 acceptance gate + determine whether current owner catalog has an adequate VISTA topic. No phase advance.

**I02 owner cross-check / acceptance:** [26 — independent direct VISTA evidence and scoped ACCEPT_WITH_RESIDUAL](./26-i02-owner-crosscheck-and-acceptance-gate.md). K3 safe no-match consistent with examined guides; other VISTA design capabilities remain TO_INVENTORY. **NEXT implementation:** [27 — I03 DAVI semantic discovery bounded brief](./27-i03-davi-semantic-discovery-implementation-brief.md). No C3/C4/C5 progression.

**I03 semantic discovery (candidate):** [28 — implementation + live](./28-i03-davi-semantic-discovery-implementation.md). Distinguishes search miss (`eligible_action_count>0`) from absence/non-enumerable catalogs. Live SHA `3d14a51046`: K4 DAVI `CAPABILITY_NOT_MATCHED` eligible=95 in 21.1s, no control-plane leak, ACT=0. `I03_ACCEPTED=NO`.

**I03 implementation and independent review:** [28 — K4 implementation/live](./28-i03-davi-semantic-discovery-implementation.md); [29 — direct DAVI MCP cross-check + scoped review](./29-i03-independent-davi-crosscheck-review.md). Direct owner: generic discovery 0/95 eligible, thematic product discovery 1 candidate. K4 scoped ACCEPT_WITH_RESIDUAL.

**I03 K2/K3 non-regression gate (candidate):** [31 — remediation + live](./31-i03-k2-k3-bounded-nonregression-remediation.md). Invalid-index recovery + index_select budget→clarify. Live SHA `9a8775018f`: K1 16.9s; K2 continuity 12.3s / 6 bullets; K3 clarify 21.8s; K4 DAVI eligible=95. `I03_ACCEPTED=NO`.

**I03 regression gate and independent acceptance:** [31 — bounded K2/K3 remediation](./31-i03-k2-k3-bounded-nonregression-remediation.md) and [32 — independent I03 ACCEPT_WITH_RESIDUAL](./32-i03-independent-nonregression-review-and-acceptance.md). K1 TÉO 16.94s; K2 six bullets, 12.31s; K3 clarifies in 21.78s; K4 DAVI discovery in 17.34s. K3 deadline-fallback code synthetic PASS but not directly exercised live. I04 generalization is next; ledger §6.271 helpdesk remains separate.

**Live orchestration decision/log validation (parallel residual):** [33 — L01–L06 authenticated live on runtime SHA `9a8775018f`](./33-live-orchestration-decision-and-log-validation.md). L01 routes to `helpdesk_read` (historical Transformômetro misroute NOT REPRODUCED) but blocks on `glpi_link_required`. L02/L06 fail on select_group/capability none → 504. L03–L05 PASS_WITH_LIMITATION / safe clarification. No functional patch; does not reopen I03 acceptance; does not start I04.

**Diagnostic L01–L06 follow-up:** [33 — live model/log evidence](./33-live-orchestration-decision-and-log-validation.md) and [34 — independent review and bounded remediation gate](./34-independent-review-live-routing-failures-and-remediation-gate.md). In eval runtime SHA 9a8775018f: L02 group none→504, L06 DAVI capability none→504, L04 projection wording; Helpdesk L01 correctly selected but GLPI link blocked count. No phase reversal or I04 auto-implementation; related priority is bounded repair of no-selection fallback and projection.

**Coordination adaptive routing reliability (boundary):** [35 — design boundary approved](./35-coordination-adaptive-routing-reliability-decision.md). R1/R3 remediation planned separately; does not authorize Q01.

**I04 provider-neutral generalization (candidate):** [36 — implementation + matrix](./36-i04-provider-neutral-generalization-implementation.md). REUSE orchestrator; EXTEND sole free-text args projection on `turn_budget_exhausted` after selection (K4 pre-fix FAIL→fix). Synthetic matrix PASS; full pytest PASS. Live post-fix recorded in doc 36. `I04_ACCEPTED=NO` until independent review. Q01 not authorized.

**I04 implementation and independent review:** [36 — code/live evidence](./36-i04-provider-neutral-generalization-implementation.md) and [37 — independent review + direct DAVI comparison](./37-i04-independent-review-and-davi-direct-crosscheck.md). I04 global REWORK: K4 live select_capability none; K3 safe clarification exceeds strict 30s; direct DAVI owner catalog reachable. Reuse pre-existing R1 selection/projection remediation (docs34–35). Q01 not authorized.

**R1+R3 none-selection and projection remediation:** [38 — implementation](./38-orchestration-none-selection-and-projection-remediation.md). Doc 35 authorized direction. Orch: selection none → `CLARIFICATION_REQUIRED` (no avoidable 504); R3 prior-excerpt framing. Full pytest PASS. Does not close R2 / I04 / Q01.

**R1/R3 independent review:** [39 — ACCEPT_WITH_RESIDUAL](./39-r1-r3-independent-acceptance-review.md). R2 semantic selection residual OPEN.

**R2 provider-neutral capability selection quality:** [40 — implementation](./40-r2-provider-neutral-capability-selection-quality.md). Coverage inquiry → sole group DISCOVERY recovery + instruction v12. Full pytest PASS. Does not accept I04 / authorize Q01.

**R2 independent review:** [41 — ACCEPT_WITH_RESIDUAL_BOUNDED](./41-r2-independent-semantic-selection-review.md). Helpdesk personal count residual remains separate (§6.271).

**R4+R5 personal ticket count and pagination:** [42 — implementation](./42-r4-r5-personal-ticket-count-and-pagination-remediation.md). EXTEND orchestrator + pure pagination/personal-scope semantics; page size ≠ total; ambiguous personal clarifies; assigned/requester without owner filters honest BLOCKED; visible COUNT aggregates pages or admits unknown. Full pytest PASS. Live linked subject `TEST_NOT_RUN`. Does not accept I04 / C3–C5 / Q01.

**R4/R5 independent review:** [43 — REWORK R5 / ACCEPT_WITH_RESIDUAL R4](./43-independent-r4-r5-review-pagination-integrity-gate.md). Unsigned `has_more` and isolated last-page totals unsafe; live select_capability timeout before owner READ.

**R45 pagination integrity + selection timeout:** [44 — implementation](./44-r45-pagination-integrity-and-selection-timeout-rework.md). First-page + contiguous + explicit completion for exact count; structural unique ticket-list capability selection for COUNT/LIST (provider-neutral). Full pytest PASS. Does not accept I04 / C3–C5 / Q01.

**R45 independent review:** [45 — ACCEPT_WITH_RESIDUAL](./45-independent-r45-pagination-and-live-ssh-review.md). Personal ticket count still INCONCLUSIVE; I04 not accepted.

**Conversational intelligence recovery:** [46 — implementation](./46-conversational-intelligence-and-orchestration-recovery.md). `applicable=false` → conversational NOT_APPLICABLE; page-slice activity omits record_count; instruction v5. Full pytest PASS. Does not accept I04 / C3–C5 / Q01.

**Semantic intelligence full recovery (candidate):** [48 — implementation](./48-semantic-intelligence-orchestration-full-recovery.md). Independent [49](./49-independent-semantic-recovery-admission-and-argument-review.md) → REWORK args. **Semantic argument rework (candidate):** [50 — implementation](./50-semantic-argument-and-task-outcome-rework.md). Removes heuristic stated-arg recovery; honest budget-skip; hypothetical admission for illustrative examples. Typed `interaction_admission` before owner listing; cold group-selection conversational reserve; schema-driven stated-argument recovery. Full pytest PASS. Does not accept I04 / C3–C5 / Q01. Independent [51](./51-independent-semantic-argument-rework-review.md) → `ACCEPT_WITH_RESIDUAL` / `REWORK_REAL_CATALOG`. **Real product owner READ + budget (candidate):** [52 — implementation](./52-real-product-owner-read-and-budget-rework.md). Owner `search_products` proven direct; DÉLIA was discarding built search args after optional index-probe budget skip; gate now proceeds when free-string args are grounded in user text. No new planner/regex/DAVI hardcode. Does not accept I04 / C3–C5 / Q01. Independent [53](./53-independent-real-product-read-and-provenance-review.md) → `ACCEPT_WITH_RESIDUAL` / provenance REWORK. **Semantic provenance + continuity (candidate):** [54 — implementation](./54-provider-neutral-semantic-provenance-and-continuity-rework.md). Free-string gate requires full token coverage (not incidental overlap); typed compare/analyze prior probe + budget stop on insufficient transform; empty synthesis recovers bullet priors; bullet excerpts stay atomic (abbreviations). Provider-neutral; no planner. Does not accept I04 / C3–C5 / Q01. **G0 bounded I04 remediation (candidate):** [62 — implementation](./62-g0-bounded-i04-remediation-compare-and-c02-budget.md). Independent review REWORK on positional `—` compare; bounded rework removes segment heuristics → typed-field gate or explicit insufficiency; C02 soft-land preserved. Does not accept I04 / Q01.

## 3. Ondas e etapas bounded — uma entrega de cada vez

| ID | Etapa | Entrega e gate de aceite |
|---|---|---|
| **I00** | **Snapshot / review do relatório 44 + contrato de contexto** | Revisar independentemente K1–K4, HEAD, runtime SHA, diferenças; rastrear backend `context` → `ConversationContextTurn` → modelo, e frontend origem/retenção/limites de turnos; classificar `PROVEN/TO_INVENTORY`. Não alterar código/persistência. Mapear CP/RQ e contrato antes de I01. |
| **I01** | **Continuidade de conhecimento contextual (K2)** | Reproduzir RED com guidance genérico de provider sintético e follow-up que pede extração de informações; estender GOAL/prior continuation existentes para distinguir reaproveitamento suficiente versus frescor exigido. GREEN: sem reconsultar owner desnecessariamente, sem copiar literalmente, sem transformar guia em FACT/AuthZ; não depender de `teo` ou nome de tool; <=30s live e testes adversariais. |
| **I02** | **Síntese fundamentada e orçamento (K1/K3)** | Mapear latências por stage; preservar headroom para seleção/apresentação sob 30s, com caminho determinístico útil e provenance-aware quando o modelo não cabe. Não liberar prosa factual livre, não mascarar `result_truncated`; GREEN para metodologia e guidance VISTA com resposta utilizável, no SHA/config avaliado. |
| **I03** | **Discovery semântico de possibilidades (K4)** | Inventariar contrato live DAVI e equivalentes OpenAPI; distinguir `no matching capability` de `catalog discoverability`. Corrigir apenas projeção/formulação comprovadamente defeituosa; nenhuma preferência MCP, metacatálogo local ou ferramenta inventada. Se contrato owner não oferecer listagem, resposta honesta e `OWNER_CONTRACT_GAP`, não hardcode. |
| **I04** | **Especialização contextual provider-neutral e generalização** | Testes bounded com TÉO, VISTA, DAVI e sibling sintético/renomeado; demonstrar orientação → próxima escolha de capability quando realmente necessária, sem exigir invocação artificial; contexto scoped por conversa, redaction, fontes/versionamento/frescor, fail-closed, 30s, ACT=0 nos evals READ. Se retenção estruturada precisar novo contrato, STOP e decisão antes de implementar. |
| **Q01** | **Caracterização e plano de extração do arquivo** | Somente **após aceites I01–I04**: mapear `orchestration.py` (~7995 linhas no snapshot), seções/funções/acoplamentos/callgraph e responsabilidades. Identificar equivalentes existentes e destino por coesão, sem implementação nem autorização automática de novos módulos. Fixar golden/contract/regression tests de seleção, evidence, policy, model proposal e governança. |
| **Q02** | **Refatoração interna incremental e sem comportamento novo** | Extrair em diffs pequenos funções puras de projeção/renderização/sanitização, validação/proveniência, instruções e helpers de seleção **apenas quando autorizado e equivalente confirmado**. Preservar um orquestrador/caso de uso e ports atuais; sem novos serviços, registros ou alterações nas autoridades. Cada diff: testes de equivalência, full backend, safety/evals e rollback claro. |
| **Q03** | **Revisão de arquitetura e fechamento** | Avaliar boundaries, coesão/complexidade, acoplamento Domain/Application/infra, regressões e generalização em SHA/config; auditoria dos resíduos e Outcome. Aceite independente `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`; não avançar C3 automaticamente. |

**Dependências:** `I00 → I01 → I02 → I03 → I04 → Q01 → Q02 → Q03`. A ordem entre I02/I03 só pode mudar com decisão registrada da coordenação. Cada etapa possui próprio CP/RQ (vincular aos IDs canônicos reais no início, sem inventar), contrato, evidência, teste e decisão independente antes da seguinte.

## 4. Acceptance & evaluation

- **K1** guia metodológico TÉO: conteúdo útil e rastreável, não dump bruto; sem inferir fatos de processo.
- **K2** follow-up TÉO: extrair perguntas/dados da metodologia já observada; `prior_evidence_sufficient` correto; evitar owner re-invoke quando dispensável; sem replay literal; <=30s.
- **K3** orientação VISTA: apresentar critérios de design suportados pelo guia; sem alegar inspeção de playlist ou executar PREPARE/ACT.
- **K4** DAVI: distinguir descoberta de possibilidades de execução de consulta; evitar falsa promessa quando não houver match.
- **Generalização**: renomeação de tool/owner e provider não MCP, prompt injection e histórico forjado, id não comprovado, autorização stale, limites de 30s, 0 ACT material sem comando/gates.
- Resultado `PASS` exige evidência real onde pertinente + scripts/holdout + task outcome; teste scripted não prova comportamento do modelo. Exceções `INCONCLUSIVE`, `TEST_NOT_RUN` ou `STALE_EVIDENCE` explícitas.

**2026-10-20 — evidência de correção, sem aceite:** o relatório [71](./71-i04-teo-guidance-generalization-full-validation.md) registra a projeção por seção, a lista de continuidade e o sibling renomeado com `kimi-k3` em provider falso. `I04_ACCEPTED` permanece `NO`. Produção não foi atualizada.

**2026-10-21 — limpeza estrutural do orquestrador:** o relatório [72](./72-orchestration-structural-cleanup-execution-report.md) (`DELIA-ORCHESTRATION-STRUCTURAL-CLEANUP-01`) removeu compatibilidade morta pós-Q02-A (constantes, regex, wrappers sem consumidores, flag experimental harness-only) e consolidou os três caminhos de invocação de modelo em `_model_stage_proposal`, sem mudança de contrato público; suíte `delia-api` 1690 PASS / 3 SKIP. `Q01_Q03`, `B1`, `I04_ACCEPTED=NO` e `C3_EXECUTED=NO` permanecem inalterados.

**2026-10-21 — frente CRI, especificação E0 fechada:** [73](./73-conversational-response-intelligence-personality-product-front.md) registra a frente Conversational Response Intelligence & Personality e [74](./74-conversational-response-intelligence-finite-implementation-roadmap.md) o roadmap de 5 gates. O relatório [75](./75-cri-e0-contract-and-decision-specification.md) (`DELIA-CRI-E0-CONTRACT-AND-DECISION-01`) fecha os contratos: ON/OFF central via `Settings`+composição (default OFF, fail-closed), recursos declarativos JSON no padrão `load_declarations`, personalidade `personality/01–04` reutilizada, `compose_presentation` estendido, e decisão de **não exigir ADR de prosa factual** no escopo E1–E4 (`selection-only` preservado; cláusula de escalonamento documentada). Documental apenas — `IMPLEMENTATION_AUTHORIZED=NO` aguardando aceite da coordenação.

**2026-10-21 — E1 implementada:** o relatório [76](./76-cri-e1-central-onoff-execution-report.md) (`DELIA-CRI-E1-CENTRAL-ONOFF-01`) entrega o controle central `DELIA_RESPONSE_INTELLIGENCE_ENABLED` — parse em `Settings`, resolução única em `root_composer`, injeção tipada no `HandleInteractiveConversationTurn` (`_response_mode` baseline|cri), default OFF, fail-closed em config inválida, observabilidade por composição e por turno (somente campos de identidade). ON seleciona o boundary sem alterar conteúdo: resultado serializado idêntico OFF/ON, zero chamadas extras ao modelo, sem E2/E3. Suíte `1713 passed, 3 skipped`. Rollback = env + restart. `I04_ACCEPTED=NO`, `C3_EXECUTED=NO` — aguarda revisão da coordenação antes de E2.

**2026-10-21 — E2 implementada:** o relatório [77](./77-cri-e2-outcome-aware-answer-execution-report.md) (`DELIA-CRI-E2-OUTCOME-AWARE-ANSWER-01`) entrega a avaliação governada de suficiência de resultado no modo ON — sucesso técnico deixa de ser confundido com resposta da tarefa. Novo módulo-folha `outcome_assessment.py` classifica fatos tipados (`answered|empty_result|envelope_only|insufficient`); o MESMO estágio de objetivo propõe `answer_requirements` (`min_items`/`ordering`/`complete_coverage`) como hipótese verificada contra evidência do owner — **zero chamadas extras ao modelo**. Insuficiência é marcada via limitação existente `insufficient_evidence` no próprio outcome (SUCCESS nunca é reescrito; todos os caminhos de render a carregam); vereditos logados `stage=outcome_assessment`. Casos A–D cobertos: "último processo" com 1 registro → `ordering_unproven`; envelope sem dados → `envelope_only`; `total=2` vs 3 pedidos → `fewer_than_requested`; leitura completa → `answered`. OFF = baseline byte-idêntico. Sem novo planner/registry/DTO público. Suíte `1756 passed, 3 skipped` (+43). `REAL_MODEL_EVALUATION=NOT_RUN` (E4). `I04_ACCEPTED=NO`, `C3_EXECUTED=NO` — aguarda revisão da coordenação antes de E3.

**2026-10-21 — E2 rework delimitado R1–R3 executado:** a revisão independente (doc 77 §9) abriu `REWORK` em ciclo único — R1 ordenação temporal aceitava evidência incompleta, R2 total disponível confundido com registros entregues, R3 instrução CRI extensa dentro de Python. `DELIA-CRI-E2-BOUNDED-REWORK-R1-R3-01` (doc 77 §10): `_temporal_orders` exige valor temporal parseável em **todos** os registros retornados (empates conservadores, conjunto de direções); `min_items` verificado contra `_distinct_delivered` — `total_count` só comprova déficit, nunca entrega; a cláusula migrou para o recurso governado `config/cri_instructions.delpi.json` + loader validado `app/infrastructure/config/cri_instruction_resource.py` (whitelist de chaves, kind/versão conhecidos, tamanho limitado, fail-closed), carregado na composição somente quando ON, com `InstructionLineage` `12+cri.1` — recurso ausente/inválido degrada o modo CRI inteiro para baseline. Suíte `1781 collected, 1778 passed, 3 skipped`. `E2_REWORK=EXECUTED`, `E2_ACCEPTED=PENDING_INDEPENDENT_REVIEW`, `I04_ACCEPTED=NO`, `C3_EXECUTED=NO`.

**2026-10-21 — E3 implementada (gates E3-G1/G2 dos resíduos E2 resolvidos):** o relatório [78](./78-cri-e3-personality-grounded-presentation-execution-report.md) (`DELIA-CRI-E3-PERSONALITY-AND-GROUNDED-PRESENTATION-01`) entrega a primeira resposta conversacional da frente — o binding edge compõe lead + evidências legíveis + avisos de limitação a partir do veredito E2 e de folhas sanitizadas do owner (`conversational_response.py`, por forma de veredito, sem templates por provider). **G1:** composição distingue `requested`/`effective` — recurso inválido/ausente com ON solicitado resolve para baseline no orquestrador, no handler e na observabilidade. **G2:** a contagem apresentada é a que o conteúdo declara — duplicatas colapsam, `presented<returned` marca `result_truncated`, `presented<requested` re-marca `insufficient_evidence`. Novo recurso governado `config/cri_presentation.delpi.json` + loader validado; `compose_presentation` v1 e frontend intocados. Suíte `1823 collected, 1820 passed, 3 skipped`; `ADDITIONAL_MODEL_CALLS=0`; OFF byte-idêntico. `E3_IMPLEMENTED=YES`, `E3_ACCEPTED=PENDING_INDEPENDENT_REVIEW`, `I04_ACCEPTED=NO`, `C3_EXECUTED=NO` — aguarda revisão da coordenação antes de E4.

**2026-10-21 — E3 rework delimitado R1–R3 executado (ciclo único):** a revisão independente (doc 78 §10) abriu `REWORK` sobre três achados de comunicação fundamentada — R1 escassez da fonte afirmada sem total autoritativo, R2 data ordenável confundida com data de alteração, R3 oferta de continuidade sem mecanismo servível. Doc 78 §11: `_shortage_key` seleciona a mensagem por fatos tipados (`total<requested` prova escassez da fonte; cobertura completa sem total prova o escopo; demais casos só afirmam retornados/apresentados); semântica temporal só é comprovada pela **chave do campo que provou a ordenação** (`_field_declares_modification` — marcador + conectivos; prosa de metadados e compostos ambíguos degradam para neutro); a oferta de continuidade foi removida — sem mecanismo servível, a omissão é o resultado correto. Vocabulário bumped para `version "2"` (v1 rejeitada → baseline fail-closed); E3-G1/G2 preservados; OFF byte-idêntico; `ADDITIONAL_MODEL_CALLS=0`. `E3_REWORK=EXECUTED`, `E3_ACCEPTED=PENDING_INDEPENDENT_REVIEW`, `E4_AUTHORIZED=NO`, `I04_ACCEPTED=NO`, `C3_EXECUTED=NO`.

**2026-10-21 — E3 aceito com residual e E4 avaliado ao vivo:** a coordenação independente aceitou o rework E3 (doc 78 §12) como `ACCEPT_WITH_RESIDUAL` — R1/R3 fechados, R2 fechado sob gate material de E4 (inferência lexical de nome de campo é heurística, não evidência de schema do owner); E4 autorizado só como avaliação bounded. O relatório [79](./79-cri-e4-real-evaluation-rollback-and-acceptance.md) (`DELIA-CRI-E4-REAL-EVAL-ROLLBACK-AND-ACCEPTANCE-01`) executou OFF/ON pareado ao vivo na stack dev local (container isolado, SHA `0af32302e9`, `moonshotai/kimi-k3`, boundary HTTP real, identidade dev documentada): `effective=cri` com recursos v1+v2 carregados; casos DAVI/DELPI **PASS** — ON rotula campos, honra a quantidade pedida (`1` → `1` + `result_truncated`) e atribui totais à fonte (`65`/`40`) sem confundir com entregues; TÉO/VISTA `TEST_NOT_RUN` — catálogos MCP rejeitam a credencial delegada em todo o ambiente (idêntico no serviço principal, condição pré-existente); gate E4-G1 `PROVEN` no contrato do owner para `updated_at` (mas sem exercício live); rollback OFF→ON→OFF restaura baseline; falha segura real provada (`requested=cri` + recurso inválido → `effective=baseline`); latência ON≈OFF; um defeito cosmético de pluralização registrado para decisão separada. Veredito do executor `ACCEPT_WITH_RESIDUAL`; `CRI_E4_ACCEPTED=NO_PENDING_COORDINATION`, `I04_ACCEPTED=NO`, `C3_EXECUTED=NO`.

**2026-10-21 — aceite operacional complementar: raiz MCP provada e evidências ao vivo dos três especialistas:** o relatório [80](./80-cri-complementary-mcp-operational-acceptance.md) (`DELIA-CRI-COMPLEMENTARY-MCP-OPERATIONAL-ACCEPTANCE-01`) fecha os gaps materiais do E4. Diagnóstico preciso da falha `mcp_authentication_failed`: classe sanitizada `RESOURCE_AUDIENCE_MISMATCH` nos três especialistas — dev resolve a audiência exigida de `PUBLIC_BASE_URL=http://localhost` enquanto o Keycloak emite a audiência canônica `https://minhadelpi.com.br/apps/<app>/mcp`; owner = config de ambiente infra; override desenhado `MCP_RESOURCE_URL` reutilizado em réplicas isoladas (containers compartilhados intactos). Ao vivo: TÉO `record_read` com ordenação `updated_at` DESC consumida ponta-a-ponta (gate temporal live), VISTA `list_playlists` (5 playlists; ON rotulada após variância de seleção), DAVI `execute_delpi_information` (3 terminais; ON atribui total 65 à fonte — owner DAVI-MCP distinto de `openapi:delpi` provado); resultado vazio real PASS nos dois modos; injeção vetor-usuário PASS; `MATERIAL_ACT=0`; `CRI OFF` default; zero linhas de runtime. Veredito `ACCEPT_WITH_RESIDUAL`; `CRI_OPERATIONAL_ACCEPTANCE=PENDING_COORDINATION`, `I04_ACCEPTED=NO`, `C3_EXECUTED=NO`.

**2026-10-21 — ativação persistente no ambiente dev + auditoria de implementação:** o relatório [81](./81-cri-persistent-activation-and-code-audit.md) (`DELIA-CRI-PERSISTENT-ACTIVATION-AND-CODE-REVIEW-01`) aplica no serviço real `delpi-delia-api` a correção de audiência proposta no doc 80 — `MCP_RESOURCE_URL` canônico versionado nos compose files (dev já trazia; base recebeu o mesmo mapeamento) e flag `DELIA_RESPONSE_INTELLIGENCE_ENABLED=true` persistida em `infra/.env` + mapeamento explícito no compose (default OFF — gate de produção preservado). Resultado: `requested=cri effective=cri` com recursos v1+v2 e `runtime_sha` pinado nos logs; TÉO/VISTA/DAVI-MCP/DELPI executam leituras reais GROUNDED; persistência provada em restart, recriação e reapply; ativação deixada ON (saudável); `MATERIAL_ACT=0`. Auditoria E1–E3: separação determinístico/semântico confirmada, sem dead code, sem prosa longa em Python; sem refactor mandatório — itens abertos (pluralização, hedging de superlativo, residual lexical E3-R2, ownership de cobertura) classificados para decisões separadas. `RUNTIME_CODE_CHANGED=NO` no código CRI; `CRI_PRODUCTION_ON=NOT_AUTHORIZED`, `I04_ACCEPTED=NO`, `C3_EXECUTED=NO`.

## 5. Limites e próximos passos

Este documento **abre somente um roadmap documental**, não aprova I01–Q03, não implanta código, não cria memory store ou contract novo, não fecha §6.235 sem review e **não** declara produção pronta. Em caso de evidência nova que invalide pressuposto, STOP.

```text
TRACK=I03_PLANNED_AFTER_I02_SCOPED_ACCEPTANCE
I00=ACCEPTED_WITH_RESIDUAL
I01_ACCEPTED=YES_WITH_RESIDUAL
I02_ACCEPTED=NO
I02_R1=DIAGNOSIS_ACCEPTED_WITH_RESIDUAL
I02_R2=ACCEPTED_WITH_RESIDUAL_SCOPED
NESTED_FIX_LIVE=EXERCISED_ON_K3_PASS_WITH_LIMITATION
LATENCY_ROOT_CAUSE=PROVEN
PERFORMANCE_FIX_IMPLEMENTED=YES_INDEX_PROBE_HEADROOM
K3_OWNER_READ_REACHED=YES
K1_K2_TEO_LIVE=FAIL_TIMEOUT
I02_R3=DIAGNOSIS_ACCEPTED_WITH_RESIDUAL
I02_R3A=EXPERIMENT_EVIDENCE_RECORDED
I02_R3B=IMPLEMENTED_ACCEPT_WITH_RESIDUAL
I02_R3B_LIVE=EVIDENCE_RECORDED
K1_TIMEOUT_EXACT_STAGE=arguments
STAGE_CAP_10S_PRODUCTION_APPROVAL=NO
ARGUMENTS_HEADROOM_PRODUCTION_DEFAULT=OFF
TYPED_CAPABILITY_GOAL_COLD_START=IMPLEMENTED
LIVE_K1_R3B=PASS_WITH_LIMITATION
LIVE_K2_R3B=PASS_WITH_LIMITATION
LIVE_K3_R3B=PASS_WITH_LIMITATION
ADAPTIVE_ROUTING_COMPLETION=PARTIAL
ADAPTIVE_ROUTING_LIVE=PASS_WITH_LIMITATION
LIVE_K1_ACR=PASS_WITH_LIMITATION
LIVE_K2_ACR=PASS_WITH_LIMITATION
LIVE_K3_ACR=PASS_WITH_LIMITATION
I02_K2_K3_QUALITY=IMPLEMENTATION_EVIDENCE_READY
I02_K2_K3_LIVE=EVIDENCE_RECORDED
LIVE_K1_QUALITY=PASS_WITH_LIMITATION
LIVE_K2_QUALITY=PASS_WITH_LIMITATION
LIVE_K3_QUALITY=PASS_SAFE_CLARIFICATION
I02_ACCEPTED=YES_WITH_RESIDUAL
I03_IMPLEMENTATION=EVIDENCE_READY
I03_LIVE=EVIDENCE_RECORDED
LIVE_K4_I03=PASS
I03_K2_K3_NONREGRESSION_LIVE=EVIDENCE_RECORDED
LIVE_K1=PASS
LIVE_K2=PASS
LIVE_K3=PASS
LIVE_K4_HOLDOUT=PASS
I03_ACCEPTED=YES_WITH_RESIDUAL
LIVE_ORCH_DIAG_33=EVIDENCE_RECORDED
LIVE_L01=FAIL_TASK_PASS_ROUTING_GLPI_LINK
LIVE_L02=FAIL_GROUP_NONE_TIMEOUT
LIVE_L03=PASS_WITH_LIMITATION
LIVE_L04=PASS_WITH_LIMITATION_RECOVER_INVALID_INDEX
LIVE_L05=PASS_SAFE_CLARIFICATION
LIVE_L06=FAIL_CAPABILITY_NONE_TIMEOUT
I04_IMPLEMENTATION=EVIDENCE_READY
I04_ACCEPTED=NO
R1_R3_REMEDIATION=EVIDENCE_READY
LIVE_L02_R1=PASS_CLARIFICATION_NO_504
LIVE_L04_R3=PASS_ORIENTACAO_FRAMING
LIVE_L06_R1=PASS_CLARIFICATION_NO_504_DISCOVERY_RESIDUAL
R2_SELECTION_QUALITY=EVIDENCE_READY
LIVE_K4_R2=PASS_DISCOVERY_GROUNDED_ELIGIBLE_95
R4_R5_PERSONAL_TICKET_COUNT=EVIDENCE_READY
PERSONAL_COUNT_LIVE=TEST_NOT_RUN
ASSIGNED_REQUESTER_OWNER_GAPS=BLOCKED
NEXT_MAIN=COORDINATION_INDEPENDENT_REVIEW
NEXT_RELATED=COORDINATION_INDEPENDENT_REVIEW_I04
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
Q01_AUTHORIZED=NO
PRODUCTION_READINESS=NOT_PROVEN
```


## Auditoria estrutural do orquestrador — somente documentação, sem aceite de mudança

- [56 — Primeiro inventário de ownership semântico](./56-orchestration-audit-semantic-ownership-checkpoint.md): 25 candidatos de remoção, substituição ou consolidação, sem autorizar deleção nem substituir gates de segurança.
- [57 — Segunda auditoria, cobertura estática integral](./57-orchestration-complete-second-pass-static-audit.md): `orchestration.py` 1–10.592 (20 regiões), 179 declarações indexadas, 17 achados suplementares, matriz preservar/revisar/consolidar e dependências. Execução/testes/SSH: `TEST_NOT_RUN`. Fonte código `8fc45e2119f3cc7b1b34a0f79bca144e5f822516`.
- Ledger [§6.299](../../evidence/execution-ledger.md): `ARCHITECTURE_DECISION_REQUIRED` para revisão de contratos congelados de grounded synthesis/comparabilidade; sem avanço de I04/C3/C4/C5/Q01. Próximo passo exige reancoragem completa, inventário de consumidores, reusable existing equivalents, contrato e testes cruzados DAVI/TÉO/VISTA/OpenAPI/non-MCP/no-tool antes de remover código.


### Decisão vinculante — ownership semântico LLM / execução determinística

- [58 — ADR aprovado de redistribuição de responsabilidades](./58-adr-llm-semantic-decision-ownership.md): `ARCHITECTURE_DIRECTION=APPROVED` (Product Master, 2026-10-19), consolidar interpretação/seleção/contexto/argumentos pelo LLM existente; enforcement de contratos, policy, Core/Domain AuthZ, provenance e ACT permanecem determinísticos e autoritativos. Fonte normativa vinculada: [49 §14.1](../../49-architecture-and-design-patterns-standard.md); ledger [§6.300](../../evidence/execution-ledger.md).
- `SELECTION_ONLY_GROUNDED_SYNTHESIS=FROZEN_PRESERVED` (§6.145); futura prosa factual gerada por LLM ou relaxamento de comparabilidade exige ADR separado. **Sem runtime diff, aprovação de remoções, testes ou avanço de C3–C5**.


### Roadmap finito de refatoração — não abrir reworks infinitos

- [59 — Plano executivo de seis pacotes](./59-orchestrator-refactoring-finite-execution-roadmap.md): `G0 I04 exit → Q01 consumer gate → Q02-A semantic ownership → Q02-B args/provenance/index → Q02-C continuity/synthesis/structural cleanup → Q03 independent closeout`. Incorpora auditorias 56/57 e ADR58; **não substitui a dependência canônica I04→Q01**.
- Cada pacote prevê uma entrega bounded e um review; no máximo **um rework** por pacote. Nova falha material depois desse ciclo = `STOP` e decisão explícita de owner/arquitetura, nunca abrir `R2/R3/R4` automaticamente. Segurança crítica nunca vira residual aceito.
- Este roteiro é **PLANNED / PENDING_PHASE_GATE**: `I04_ACCEPTED=NO` e `Q01_AUTHORIZED=NO` no HEAD documental; não autoriza código, deploy ou avanço de fase. O primeiro item é **G0 — decisão conclusiva de I04** com bloqueios externos classificados separadamente.


### Pesquisa concluída no GPT antes da refatoração — sem loops de inventário no Cursor

- [59 — roadmap executivo fechado (seis pacotes)](./59-orchestrator-refactoring-finite-execution-roadmap.md): G0→Q01→Q02-A/B/C→Q03, até um rework delimitado por pacote; dependências de fase preservadas.
- [60 — inventário pré-Q01 realizado pelo GPT](./60-pre-q01-consumers-contracts-tests-inventory.md): 42/42 achados → código, callers, contratos, owner, suites e decisões de reuso; classificador de linguagem adjacente identificado.
- [61 — evidências G0 e handoff para Cursor somente executar refatoração](./61-g0-evidence-prepared-and-cursor-only-implementation-handoff.md): blockers I04, pacotes de código delimitados, RED/DoD, 17 classes de teste e STOP gates. Cursor só executa code/test/live após autorização, e uma busca residual para drift local, não outro inventário amplo.
- [Ledger §6.302](../../evidence/execution-ledger.md): levantamento `PROVEN` na fonte, limitações `TO_INVENTORY/TEST_NOT_RUN` e Q01 não autorizado.

### G0/I04 live validation pointer

 **Independent live validation 2026-10-19:** see [62 live section](./62-g0-bounded-i04-remediation-compare-and-c02-budget.md) / ledger §6.311 — `I04_ACCEPTED=NO`; C02 task FAIL; G0 compare fail-closed PASS live.

**2026-10-20 — coordenação, evidência live I04 não publicada:** executor reportou em runtime com hash de `orchestration.py` corrigido: K1 FAIL sem TÉO (HTTP 200, NON_GROUNDED), K2 INCONCLUSIVE (HTTP 502 e K1 sem evidência), K3 FAIL sem VISTA por budget, K4 FAIL sem DAVI por budget, G1 TEST_NOT_RUN; sem logs de estágio porque leitura de `docker logs` não retornou. Esses resultados são evidência de OUTCOME reportada, ainda não corroborada por traces internos; não provam causa raiz ou regressão do empacotador. Estado de coordenação: `I04_ACCEPTED=NO`, `C3_EXECUTED=NO`, `REWORK_REQUIRED_FOR_FUNCTIONAL_GATE=YES`, `CODE_REWORK_AUTHORIZED=NO`. Próximo passo: diagnóstico estritamente observacional dos quatro casos/telemetria já existente, sem nova bateria nem patch; separar admissão/seleção/latência/erro de transporte, verificar runtime/config/owner availability e somente então decidir correção bounded. G1 segue separado em harness isolado, sem produção.


### Coordination state snapshot — 2026-10-20 (Product Master)

**Scope:** preserve current state and await the next Product Master instruction; this is **not** an I04 acceptance, C3 phase change, implementation approval, test authorization, or permission to modify production. The finite semantic-orchestrator refactor Q01–Q03 is technically **CLOSED_WITH_RESIDUAL**; Q03 independent review verdict `ACCEPT_WITH_RESIDUAL` (report 67, roadmap 59 §22). Semantic ownership direction remains LLM proposes, DÉLIA governs and validates technical/policy boundaries, Domain API/owners provide authoritative data. No blanket claim that all leftover heuristics or all model-quality defects have been eliminated.

**Observed functionality:** READ consultations with TÉO, VISTA and DAVI have succeeded in bounded live samples (report 69: K3/K4 PASS; K1/K2 PARTIAL); conceptual SIPOC, hypotheses, conversational comparison and GROUNDED OpenAPI READ succeeded in earlier real-model tests (reports 63/66). Guided clarifications, prior-turn continuity and missing-argument resolution have implementation/test evidence, but the complete ask-for-missing-field → user supplies value → same capability authoritative answer scenario is **not claimed universally proven live**. K1/K2 presentation fixes and isolated G1 real-model test were committed (report 71, SHA `87ee95df449005ef0e95d7ccbac2ac91772112b4`; 1693 PASS/3 SKIP executor reported). G1 observed selection under both original and renamed labels in one isolated pair but an unintended subsequent pair resulted in `NOT_APPLICABLE` for both; repeatability residual, no production MCP affected.

**Current I04 acceptance:** `INCONCLUSIVE`, `I04_ACCEPTED=NO`; later real runtime sample reported K1 no specialist, K2 HTTP 502, K3/K4 no specialist and budget end, without retained NDJSON/stage traces. These **observed outcome failures remain open**, but their admission-versus-selection root cause is `INCONCLUSIVE` and no implementation fix is authorized. Trace retrieval concluded inconclusive because assessment used JSON (no ActivityEvent) and container stdout was unavailable; a future authorized evaluation could use existing NDJSON stage events. The local report 72 and ledger §6.348–349 were reported as **not published** after git fetch stalled; do not silently mark them published or rewrite ledger based on an empty connector result.

**Remaining architectural/evidence limits:** B1 single ticket READ/QUERY lexical shortcut remains preserved and unresolved, risk non-critical per Q03; HTTP 404 projection and typed owner comparison lack current real-runtime coverage; current K1/K2 owner-live fix evidence and robust sibling repeatability are limited. No new code changes, broad audit, endless retries, owner-domain validators, or further tests are requested here. `C3_EXECUTED=NO`, `PRODUCTION_READINESS=NOT_PROVEN`, `AUTOMATIC_MODEL_RETRY=NOT_AUTHORIZED`; preserve 30s global deadline, post-orchestration 12s fallback, Core/Domain authority, selection-only factual synthesis, READ/PREPARE/ACT boundaries and safety gates.

```text
SEMANTIC_REFACTOR_Q01_Q03=CLOSED_WITH_RESIDUAL
Q03_VERDICT=ACCEPT_WITH_RESIDUAL
I04_ACCEPTED=NO
I04_GATE=INCONCLUSIVE
C3_EXECUTED=NO
B1=UNRESOLVED_DEFERRED
I04_OWNER_SELECTION_ROOT_CAUSE=INCONCLUSIVE
FURTHER_CODE_REWORK_AUTHORIZED=NO
PRODUCTION_READINESS=NOT_PROVEN
NEXT=AWAIT_PRODUCT_MASTER_COMMAND
```


### Independent coordination review — Structural Cleanup 01 (2026-10-21)

Reviewed published `main` SHA `352f1bd0524d5a37f069e82489d868266b2f65ab` against base `fe61449102a35d2636bd58047a019753f2ad6fd9`, source and [report 72](./72-orchestration-structural-cleanup-execution-report.md). **Verdict: `ACCEPT_WITH_RESIDUAL` for structural scope only.** GitHub compare: orchestration.py 87 additions/250 deletions, one remaining `self._invoke_model.execute` through `_model_stage_proposal`, removed compatibility symbols/experimental flag absent, B1 retained, separate candidate lineage/validation preserved. Executor reports post-change suite `1690 PASS / 3 SKIP`; independently verified published code statically, **not** independently rerun tests. Published SHA followed a rebase with unrelated controllership-finance documentation; full 12-file compare is not exclusively cleanup scope (report's 7 touched source/test files + documentation). No live-model regression and no post-rebase published-SHA suite demonstrated: `TEST_NOT_RUN`; cannot claim production functional equivalence. No code or public contract changes in this review. Do not reopen Q01–Q03 or claim I04 accepted. `I04_ACCEPTED=NO`, `C3_EXECUTED=NO`, `B1=UNRESOLVED`, `PRODUCTION_DEPLOY_AUTHORIZED=NO`. Structural cleanup package CLOSED_WITH_RESIDUAL, no automatic rework; future deployment/eval gates separate.


### New product front — Conversational Response Intelligence & Personality (2026-10-21)

Product Master registered [73 — product front](./73-conversational-response-intelligence-personality-product-front.md) after real TÉO, DAVI/API DELPI and VISTA MFE interactions showed a gap between consulted records and useful, natural user-facing answers. Scope: outcome-aware responses, evidence-grounded human-readable presentation, reuse of existing DÉLIA personality specifications and shared components, finite acceptance matrix. `PERSONALITY_SPECS=TO_INVENTORY`, `RICH_FACTUAL_PROSE=ARCHITECTURE_DECISION_REQUIRED` (ADR 58 selection-only is frozen), `IMPLEMENTATION_AUTHORIZED=NO`; next bounded specification task `DELIA-CONVERSATIONAL-RESPONSE-INTELLIGENCE-SPEC-01`. This does not reopen Q01-Q03 or alter I04/C3 gates.

**2026-10-21 — interpretação semântica de campos sem hardcode lexical:** o relatório [82](./82-cri-semantic-field-interpretation.md) (`DELIA-CRI-SEMANTIC-FIELD-INTERPRETATION-AND-AUTHORITY-ALIGNMENT-01`) remove `_field_declares_modification` e seus conjuntos de tokens: o estágio de goal existente pode propor `ordering_semantic` (vocabulário de evento delimitado + campo + citação verbatim da descrição da capability); `verified_ordering_event()` só confirma quando o campo proposto é o que de fato prova a ordenação nos registros retornados E a evidência citada é substring verbatim do contrato declarado pelo owner. Composição passa a consumir `ordering_event`; recurso de instrução v2 (v1 ainda válida para rollback); log `semantic_proposed`/`ordering_event`. Suíte completa PASS; live TÉO GROUNDED com abstenção correta do modelo (nenhuma descrição de owner declara semântica de campo → lacuna contratual registrada; unlock legítimo = evolução de contrato no owner, decisão separada). `LEXICAL_HEURISTIC_REMOVED=YES`, `NEW_MODEL_STAGES=0`, `OFF_PARITY=PASS`, `CRI_PRODUCTION_ON=NOT_AUTHORIZED`, `I04_ACCEPTED=NO`, `C3_EXECUTED=NO`.
