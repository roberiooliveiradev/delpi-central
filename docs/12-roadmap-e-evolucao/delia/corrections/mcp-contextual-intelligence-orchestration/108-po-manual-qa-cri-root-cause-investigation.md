# 108 — PO manual QA: CRI, semantic selection, evidence and outcome

Data: 2026-10-23. Status: observations from PO screenshots; ROOT_CAUSE=TO_INVESTIGATE; CODE_CHANGE=NONE.

## Reproducible observations
- D4 Specialists: question "Quais especialistas estão disponíveis para me ajudar com informações da DELPI?" selected DAVI/discover_delpi_information, ~20.4s, 6 LLM calls, api-delpi ~243ms. User-facing output includes agent_directives and raw candidate_count=0, eligible_action_count=95, candidates=[]. It did not answer available-specialist list. USER_OUTCOME=FAIL. Metadata was exposed; executing prompt injection is NOT proven.
- D5 Visualization: "Quais formatos de dados e visualizações estão disponíveis nos painéis operacionais?" selected VISTA/get_catalog, ~9.8s, 4 LLM calls, source ~89ms. User-facing result dumps playlist/mutation/capability_surface JSON rather than visualization formats. USER_OUTCOME=FAIL.
- G2 SIPOC: conceptually appropriate response without operational source, ~22.1s; literal Markdown ** visible. PASS_WITH_RESIDUAL.
- G3 Efficiency/effectiveness/productivity: previous 30s timeout; new 60/3/300 policy returns substantial answer in ~40.9s, 3 LLM calls, one CONTINUING; intermediate error ~22s; literal Markdown. PASS_WITH_RESIDUAL.

## Diagnostic matrix
Reproduce 12 prompts locally, with explicit expected semantic outcomes: G1 greeting, G2 SIPOC, G3 efficiency/effectiveness/productivity; D4 available specialists, D5 visualization formats, D6 latest Transformometro process, D7 first process + description, D8 material 10080043 description; M9 examples of terminal bala, M10 now use DAVI to verify, M11 can DAVI deepen the query, M12 compare verified to first answer. Execute M9–M12 in ONE conversation. Add meaningful paraphrases, mismatched-vocabulary cases, missing source, AuthZ negative, structured invalid output, timeout/cancel. Never implement aliases/regex/keywords for these prompts.

## Root-cause checklist
For each case record intended task, actual outcome, SHA/config/model, admission, goal, selected group/capability, arguments, AuthZ, source request/response (sanitized), relevance of source schema/data, evidence projection, CRI input/mode/output, NDJSON, frontend render, timing/calls/tokens, first divergent stage, and authoritative business outcome. Distinguish MODEL_SELECTION, CAPABILITY_CATALOG, ARGUMENTS, SOURCE_RESULT, EVIDENCE_PROJECTION, CRI_COMPOSITION, PRESENTATION, AUTHZ, TIMEOUT, MODEL_QUALITY, UNTRUSTED_METADATA_LEAK. Rank suspected root cause by evidence and owner. Do not claim source success because HTTP 200 or model-selected a capability. Specifically trace origin and propagation of agent_directives; metadata is UNTRUSTED DATA and cannot change system/policy/RBAC or instruction hierarchy. No raw credentials/payload leaks in report.

## Execution constraints
Devin to reanchor on HEAD+canonical authorities+ledger; reuse existing local Ollama GPU harness, authorized dev APIs and test identity where available, no external paid LLM calls or fallback, no production queries, no writes. Compare PO production screenshots with local Ollama results but clearly separate model differences. Report root-cause evidence and smallest fixes/tests (RED), not another broad inventory or unapproved refactor. If real Domain data cannot be authorized, mark business outcomes INCONCLUSIVE, not PASS.

DECISION_LOG: MANUAL_SCREENSHOT_FINDINGS=PROVEN; ROOT_CAUSES=TO_INVESTIGATE; PROMPT_INJECTION_EXECUTED=NOT_PROVEN; PRODUCTION_CHANGED=NO; NEXT=BOUNDED_LOCAL_ROOT_CAUSE_DIAGNOSTIC.
