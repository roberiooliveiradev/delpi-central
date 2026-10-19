# DÉLIA — Roadmap bounded · Inteligência contextual MCP e organização do orquestrador

**DATA:** 2026-10-19 (roadmap state refresh; original baseline remains historical)
**TRACK_ID:** `DELIA-C3-MCP-CONTEXTUAL-INTELLIGENCE-AND-ORCHESTRATOR-QUALITY-01`
**STATUS:** `I00_ACCEPTED_WITH_RESIDUAL / I01_ACCEPTED_WITH_RESIDUAL / I02_ACCEPTED_WITH_RESIDUAL_SCOPED / I03_IMPLEMENTATION_PLANNED / I04–Q03_PLANNED`
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
I03_ACCEPTED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
PRODUCTION_READINESS=NOT_PROVEN
```
