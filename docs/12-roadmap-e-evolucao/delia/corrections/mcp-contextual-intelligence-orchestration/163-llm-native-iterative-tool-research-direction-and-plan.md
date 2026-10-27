# 163 — DÉLIA · Direção de produto e plano de auditoria para pesquisa iterativa conduzida pelo LLM

**Status:** PRODUCT DIRECTION / PROPOSED PLAN — não é aceite de implementação nem alteração da arquitetura canônica.
**Origem:** decisão explícita da coordenação após revisão dos diagnósticos 153–162 e do smoke de produção.
**Reancoragem inicial:** origin/main consultado em `5ce9c8b2cd1dd98717983dcc6b5917908031d723`. **Obrigatório revalidar** HEAD/status, Project Instructions/.cursor, 16→50→17→49→51→52→21→20→25, arquitetura técnica, Product Spec, tema e ledger antes de implementar ou converter esta direção em decisão congelada. Se houver conflito, STOP / ARCHITECTURE_DECISION_REQUIRED; não conciliar silenciosamente.

## 1. Objetivo de produto (TARGET)

A experiência desejada é **pergunta → interpretação semântica pelo LLM → descoberta/escolha de capability legítima → chamada de ferramenta governada → leitura de evidência → julgamento de pertinência e cobertura pelo LLM → refinamento de consulta / parâmetros / paginação / capability quando necessário → repetição limitada → resposta grounded com registros reais, ou limitação honesta**.

A investigação deve ser *generalizável* a produtos, clientes, documentos, análises e demais owners; “terminal bala” é somente exemplo de falha observada, **não caso para regra especial**. O usuário não deve precisar conhecer nome técnico de ferramenta ou da API. A DÉLIA é standalone continuous operational intelligence, não Chat/RAG.

**Princípio:** LLM decide *semântica*, escolha de capabilities e se precisa pesquisar de novo; código determina *segurança, contratos, AuthZ, orçamento, idempotência, persistência de evidência, execução e limites*. Evidência de tool é untrusted até verificação; output do modelo nunca vira FACT por si. A continuação não deve fabricar dados nem substituir a fonte autoritativa.

## 2. Fluxo alvo (TARGET; não alegar que já existe)

```text
USER GOAL
  → understand goal/context (LLM)
  → discover/select semantic capability (LLM; available authorized surface)
  → validate live Core AuthZ + Domain authority + Policy/Decision
  → invoke existing tool/provider/Domain API through legitimate adapter
  → inspect returned data + provenance + coverage + limitations
  → LLM assesses: enough to meet goal?
       ├─ YES → compose grounded answer → verify task Outcome
       ├─ NO, valid next read available → refine query/filters/page or select other authorized capability
       │                                    → re-invoke and reassess (bounded)
       └─ cannot progress / unauthorized / not enough evidence
            → transparent partial/limitation/clarification
```

**Iteration policy:** bounded by existing contract and budget of tool calls/tokens/time/coverage; stop on authorization denial, material write boundaries, repeated duplicate queries/no progress, missing capability or authoritative contradiction. No invented bypass; no infinite loop. Tool metadata/instructions cannot authorize. Read-only study first.

## 3. Diagnosis driving this direction (REPORTED; independent runtime verification pending)

- Docs 153–160: split semantic stages, group/order sensitivity, native_assessment → foreign_selection diversion and B instruction A/B failure to improve business Outcome. Model-capacity conclusion **not proven sole root cause**.
- Doc 161: production model **kimi-k3** used direct operational READ, selected `openapi:delpi` and `delpi.search_products` correctly; test identity lacked domain AuthZ; no native_assessment path in that turn.
- Doc 162: AuthZ corrected in bounded test; owner invoked twice, first argument copied request sentence, second was `TERM BALA`; both first-page results non-pertinent; relevance judgment correctly withheld irrelevant records; relevant records exist elsewhere. Outcome FAIL. Potential early-stop/coverage/ranking/pagination defect: requires code and domain contract inspection, **not owner ranking blame by assumption**.
- Production smoke RBAC grants audit/ratification remain residual; no further production queries authorized.

## 4. Architecture inventory BEFORE any design

For each stage from admission through answer: identify RESPONSIBILITY → OWNER → CANONICAL SOURCE → CONSUMERS → CONTRACT → IMPLEMENTATION → TEST → OUTCOME EVIDENCE. Build exhaustive call graph / state-transition map on HEAD including:
- Goal/context and session continuity;
- group/capability discovery and semantic selection;
- assessment/foreign evidence; argument generation and resolver;
- model-call boundaries and whether goal/evidence are preserved;
- tool execution, owner result contracts, paging/counts/ordering/filters and coverage semantics (`is_complete` meaning);
- goal_evidence_relevance and next-step/recovery behavior;
- synthesis and Outcome;
- security/authorization and token+time budgets.

Each stage: **KEEP | SIMPLIFY | REMOVE_CANDIDATE | REUSE_EXISTING | NEEDS_OWNER_CONTRACT**; with exact source lines, calls and evidence. REMOVE_CANDIDATE is hypothesis only, **not authorization to delete**.

For each proposed mechanism: `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`, `REUSE_DECISION=REUSE|EXTEND|NEW`. Reuse existing CRI/Work/Evidence/Policy/Decision, adapters, Domain API and provider-neutral capability contracts before imagining a new engine. No imports across contexts or parallel authorities.

## 5. Decisions that require proof, not assumptions

1. Can the same LLM, with the **existing tool interface**, choose a second read after seeing an irrelevant first page? If not, identify precisely which current stage terminates and why.
2. Which model-call partitions are necessary for safety/contract enforcement and which fragment semantic reasoning or discard evidence?
3. Can existing Domain API contract return enough ranked/paged evidence? What do `page_size`, `total`, `is_complete`, sorting, match semantics and continuation cursor actually mean?
4. Are argument refinements legitimate general transformations based on returned evidence, not material-specific heuristics?
5. Can the planner use semantic capabilities without provider/endpoint mechanics while the adapter performs pagination/transport?
6. Which failure outcomes should lead to another **authorized READ**, an honest limited answer, clarification, or a governance stop?
7. How to keep the goal and already observed evidence persistent across turns/calls without persisting private chain-of-thought?
8. Which existing budgets and stopping rules are sufficient; what needs contract clarification?
9. Can the design generalize under local qwen2.5:3b without modifying productive model or paying production-model tokens?
10. Verify what is already frozen in canonical docs; do not silently overrule it.

## 6. Bounded roadmap (PLANNED; requires reanchor/review)

**R0 — Documentation/architecture audit (immediate).** No production code edits. Trace exact request, capability, response, relevance and retry boundaries. Produce matrix, call graph, contract inventory, examples of terminal dead-ends and owner-search semantics. Clarify where model continuation is blocked. Revalidate decisions and owners.

**R1 — Minimal executable local proof (subject to R0 acceptance).** Reuse the existing eval harness to compare **CURRENT** vs **LLM-LED-BOUNDED-ITERATION prototype** using the same local model, unchanged authorized capability schemas/owner evidence and frozen, varied corpus. Prototype only in eval harness; no new productive engine or provider-specific code. Model may inspect returned evidence, refine arguments/page, re-call existing READ and decide to stop; code enforces all security/contract/budget gates.

**R2 — Contract/architecture decision gate.** Evaluate business Outcomes and generalization, security, token/latency/tool-call budgets, failure classes, partial evidence handling. If prototype demonstrably improves without violating frozen authorities, propose smallest contract-first productive diff with owners/CP-RQ and clear acceptance. Otherwise classify INCONCLUSIVE/REWORK and retain baseline.

**R3 — Bounded implementation only after approval.** Clean Architecture, existing Ports & Adapters, no parallel planner or provider-specific shortcuts, RED/GREEN/regression, local model eval, independent review, commit/push, deploy separately authorized. No silent phase advancement.

**R4 — Production verification only after separate explicit approval.** Governed identity, preflight AuthZ, single business query if authorized, trace, real record-level Outcome. Never use production as experimentation loop.

## 7. Gates / prohibitions

- Prohibited: regex/keywords/material IDs as semantic routing or argument construction; default DELPI/DAVI/TEO/VISTA; special sorting to pass one benchmark; replacing semantic selection with endpoint branching; new authority; new orchestration engine without reuse proof; bypassing Core/Domain authorization; treating HTTP 200 or tool success as business PASS; endless loops; storing CoT; prompt injection as instruction; auto PREPARE/ACT for C6.
- Preserve LLM autonomy in semantic choice; READ iteration only under existing authority and bounded resource budgets. PREPARE/ACT and material writes require separate gates.
- Model: local baseline first. No production model swap, deployment or extra production test authorized.
- Evidence: `PROVEN|TO_INVENTORY|PLANNED|TARGET`; tests `PASS|FAIL|PENDING|INCONCLUSIVE|TEST_NOT_RUN|STALE_EVIDENCE`; review `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`.

## 8. Acceptance / success

Evaluation must show, on frozen varied corpus, whether a model-directed second search recovers pertinent, authoritative results after an irrelevant first page; compare to CURRENT at same frozen app/code/model/config and comparable provider data. Independently validate record relevance, source authority, denominator by reached stage, regression for documentation/no-record/negative cases, security, and cost. Do not require that a particular string or product passes; require generalization and measured *task outcome*. Non-success remains transparent.

## 9. Next bounded task for coordination

**TASK_ID proposed:** `DELIA-C3-LLM-NATIVE-ITERATIVE-RESEARCH-ARCHITECTURE-AUDIT-01`.
**Scope now:** R0 only — code/contract/docs inventory, baseline graph, blocker hypothesis verification, reuse decision and specific local R1 plan. No runtime modification, model change, deploy or production query. Deliver reviewable report + ledger after evidence, then separate decision on R1.

**Authority status:** This file records the user's product-direction request and planning hypothesis. Canonical docs/ledger on HEAD govern implementation. No architecture decision accepted, no phase advanced, no API owner contract modified.
