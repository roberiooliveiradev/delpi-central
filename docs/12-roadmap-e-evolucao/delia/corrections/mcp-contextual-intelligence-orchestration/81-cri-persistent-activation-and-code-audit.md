# 81 — CRI persistent activation (dev/homologation) + implementation audit

**Date:** 2026-10-21. **TASK_ID:** `DELIA-CRI-PERSISTENT-ACTIVATION-AND-CODE-REVIEW-01`. **Order executed:** ACTIVATE first, AUDIT after. **Scope:** persistent ON in the authorized dev/homologation environment + technical audit of the CRI implementation. **Not:** production rollout, refactoring, or new implementation.

Follow-up to [79 — E4 real evaluation](./79-cri-e4-real-evaluation-rollback-and-acceptance.md) and [80 — complementary MCP operational acceptance](./80-cri-complementary-mcp-operational-acceptance.md).

## Report A — Persistent activation

```text
CRI_ACTIVATION_REPORT

BASE_HEAD=2f6cb084dbae9db06affb3b59fe6c5a0a264e5c4
RUNTIME_SHA=2f6cb084dbae9db06affb3b59fe6c5a0a264e5c4 (pinned via DELIA_RUNTIME_SHA, logged at boot)
ENVIRONMENT=local dev/homologation docker stack (DELIA_ENV=development, infra_delpi-network)
DEPLOYMENT_OWNER=infra/docker-compose.dev.yml + gitignored infra/.env — canonical dev procedure
                 (README-ambiente: docker compose -f infra/docker-compose.dev.yml up -d)

MCP_AUDIENCE_CONFIGURATION=MCP_RESOURCE_URL=<canonical public URL> per specialist —
                 transformometro-api / tv-dashboard-api / api-delpi. The mapping already
                 existed in docker-compose.dev.yml (commit cc65cc6388, C3-MCP-INTEROP-01R1B);
                 the running stack was stale/mixed (specialists had been created from the
                 base docker-compose.yml which lacked the mapping → PUBLIC_BASE_URL=localhost
                 resolution → RESOURCE_AUDIENCE_MISMATCH, as diagnosed in doc 80 §2).
                 The same mapping was added to docker-compose.yml so a base-file recreate
                 cannot reintroduce the drift.
MCP_AUTH_RESULT=PASS — tools/list + tools/call HTTP 200/202 on all three specialists
                 from the real delpi-delia-api service (RFC 8693 delegated exchange,
                 canonical aud, mcp:tools). groups=4 advertised to the selector.

FEATURE_FLAG_PERSISTED=YES — DELIA_RESPONSE_INTELLIGENCE_ENABLED=true in infra/.env
                 (gitignored, non-secret) + explicit environment mapping added to
                 docker-compose.dev.yml and docker-compose.yml (convention ${VAR:-};
                 default stays OFF — production gate preserved).
REQUESTED_MODE=cri
EFFECTIVE_MODE=cri (cri_instruction_resource v1 sha256 7e3c5515… +
                 cri_presentation_resource v2 sha256 c947616d… loaded; logged per boot)

RESTART_VERIFIED=YES — docker restart → requested=cri effective=cri
CONTAINER_RECREATION_VERIFIED=YES — compose up recreated delia-api twice; both boots
                 loaded v1+v2 resources and resolved effective=cri
REAPPLY_VERIFIED=YES — no-change compose up -d idempotent (config hash stable)
ROLLBACK_AVAILABLE=YES — governed: unset/empty DELIA_RESPONSE_INTELLIGENCE_ENABLED
                 in infra/.env + recreate; mechanism already proven live in E4
                 (requested=cri + invalid/absent resource → fail-closed baseline).

TEO_LIVE=PASS — real turn on the real service: mcp:teo record_read, GROUNDED,
                 OBSERVATION; conservative insufficient_evidence hedge on the
                 superlative (coverage_unproven — bounded page cannot prove global
                 "último"). Temporal ordering evidence live (owner updated_at DESC).
VISTA_LIVE=PASS — mcp:vista list_playlists, GROUNDED; coverage hedge on open list.
DAVI_LIVE=PASS — mcp:davi execute_delpi_information, GROUNDED; CRI presentation:
                 "Aqui estão 3 exemplos" + labeled fields + "A fonte informa 65
                 registros no total" (DAVI-MCP owner, distinct from openapi:delpi).
DELPI_LIVE=PASS — openapi delpi.search_products, GROUNDED; labeled + "A fonte
                 informa 55324 registros no total".

GROUNDING=PASS — all delivered content verbatim owner leaves; hedged verdicts
                 honest; nothing invented
LATENCY=24–30s per turn (model-bound: stage proposals 2–9s each via OpenRouter
                 kimi-k3; provider_invoke <0.5s). DELIA_MODEL_STAGE_TIMEOUT_SECONDS
                 aligned to the sanctioned prod-file default 30 (was unmapped in
                 dev → code default 10s, which killed stage calls); global
                 DELIA_TURN_BUDGET_SECONDS=30 unchanged and respected.
SECURITY=PASS — no writes executed (READ/DISCOVERY only), MATERIAL_ACT=0,
                 no secrets/tokens printed, delegated auth path intact.

CRI_REMAINS_ENABLED=YES — healthy activation left ON on delpi-delia-api
PRODUCTION_GATE=PENDING — this activation covers dev/homologation only; the prod
                 compose mapping defaults the flag OFF and requires the separate
                 rollout/rollback authorization. Identifier of the prod surface:
                 infra/docker-compose.yml delia-api (Dockerfile.prod image,
                 DELIA_ENV=production) deployed via local-first-deploy remote pull.
ACTIVATION_VERDICT=PASS — persistent ON verified across restart + recreation.
```

## Report B — Implementation audit (E1–E3 + E4 integration)

**Audited SHA:** `2f6cb084dbae9db06affb3b59fe6c5a0a264e5c4` (`origin/main`).

**Files reviewed:** `outcome_assessment.py` (322), `conversational_response.py` (453), `cri_instruction_resource.py` (306), `cri_instructions.delpi.json` (v1), `cri_presentation.delpi.json` (v2), CRI wiring in `root_composer.py` (~60 lines), CRI edge in `orchestration.py` (~350 of 10 532 lines), `handle_interactive_turn.py` response-mode propagation, `paginated_result_semantics.py` (801, pre-CRI C4 module), test files `test_cri_e1/e2/e3` (51+ tests).

### Architecture findings

- **Clean leaf separation is real.** `outcome_assessment.py` is a pure deterministic leaf (typed facts → verdict; no provider names, no model calls). `conversational_response.py` is a pure composition leaf (verdict + sanitized leaves + validated vocabulary → text). `cri_instruction_resource.py` is a single fail-closed loader with kind/version allowlists, section/entry/placeholder bounds and content hashes. `root_composer` resolves `requested`/`effective` once and injects typed values — never strings parsed at edges. This matches ADR 58 and the frozen selection-only contract.
- **Deterministic vs semantic split is correct.** The model proposes `answer_requirements` as a *hypothesis* inside the existing goal stage (clause text injected only when ON); the runtime verifies each declared requirement against typed evidence. No requirement is ever assumed by the runtime.
- **Single edge, single verdict.** `_outcome_facts → assess_outcome → _apply_outcome_assessment → _compose_cri_response` run once per outcome at the binding edge (orchestration.py ~5916); the same verdict feeds both the limitation marker and the presentation. No duplicated assessment.
- **Observability adequate.** Boot: resource ids+versions+sha256 + `requested/effective/config_source/runtime_sha`. Per turn: `stage=outcome_assessment decision=… reasons=…`, `stage=cri_response decision=composed|fallback presented=N delivered=M`, `stage=response_mode`. Sufficient for forensics.

### Duplications / couplings

- `_temporal_orders` vs `ordering_proof_fields` — both wrap `_temporal_proofs`; the former returns direction names, the latter direction→field. Both consumed; the duplication is a thin view, not logic — micro-simplifiable but harmless.
- `_outcome_facts` re-derives coverage from `extract_pagination_envelope` fields (`has_more`/`total_count`) — semantics that `paginated_result_semantics.py` already owns (CountResolutionKind etc.). Legitimate consolidation candidate; bounded and requires owner alignment (C4 module).
- **Known coupled heuristic:** `_field_declares_modification` + `_MODIFICATION_FIELD_TOKENS`/`_TEMPORAL_FIELD_CONNECTIVES` lexical field-name inference (E3-R2 residual — lexical inference is not owner-schema evidence; deliberately conservative, degrades to neutral). Field-name vocabularies are the only provider-lexical coupling introduced by CRI.
- Long instruction/prose text: **none embedded in Python** — instruction clause and all presentation text live in governed JSON (compliant with the roadmap convention). PT-BR scalar rendering in `_cri_scalar_text` ("sim"/"não", date format) is presentation formatting, small and bounded.

### Dead code / size / testability

- No dead code found in the CRI modules — every public helper has a real consumer (verified by call-site grep). `parse_temporal_value`, `ordering_proof_fields`, `distinct_delivered_count` are deliberate public views over private primitives.
- `orchestration.py` at 10 532 lines remains the known pre-existing condition (§6.235/Q01 lineage — CRI added ~350 lines). The CRI helpers are correctly *in* orchestration where the sanitization/extraction helpers live; splitting them into a new module would drag `_sanitize_renderable`, `_canonical_key`, `_FIELD_CLAUSE_LABELS`, `_record_identifier` across a boundary — not justified by cohesion gain. No broad orchestrator refactor recommended.
- Testability: leaves are pure functions — E2 suite has 51 tests covering verdicts, requirement parsing, ordering proofs; E3 suite covers composition shapes, shortage-key selection, fail-closed vocabulary.
- Performance: deterministic stages add ~0ms; `ADDITIONAL_MODEL_CALLS=0`. The observed 24–30s latency is model-stage bound (pre-existing orchestration cost), not CRI.

### Known open defects (for separate bounded decisions)

- **Pluralization:** `examples_fulfilled` template `"Aqui estão {count} exemplos:"` has no plural construct → observed live as `Aqui estão 1 exemplos` (E4). Fix needs a vocabulary variant or plural placeholder — REQUIRES_DECISION.
- **ON superlative hedging:** for "o último X" questions the verdict `coverage_unproven` withholds the proven top record instead of presenting it with the caveat — grounded but conservative. Improvement candidate, REQUIRES_DECISION (presentation policy, not a bug).

### Classification

```text
AUDITED_SHA=2f6cb084dbae9db06affb3b59fe6c5a0a264e5c4
FILES_REVIEWED=11 (5 CRI modules/resources + wiring + handler + pagination + tests)
AUTHORITIES_REVALIDATED=docs 73–80, ADR 58, delia-execution-protocol, E4/complementary reviews

KEEP=outcome_assessment.py; conversational_response.py; cri_instruction_resource.py;
     cri_instructions.delpi.json v1; cri_presentation.delpi.json v2;
     root_composer requested/effective resolution; per-turn stage logs
SIMPLIFY=_temporal_orders could delegate to ordering_proof_fields().keys() (micro; optional)
CONSOLIDATE=coverage derivation in _outcome_facts vs paginated_result_semantics owner
           (bounded; needs C4-module owner decision)
MOVE=none required — CRI presentation helpers correctly co-located with sanitization helpers
REMOVE=none — no dead code found
REQUIRES_DECISION=pluralization template fix; superlative-hedging presentation policy;
                 lexical field-semantics residual (E3-R2); coverage-derivation ownership

PROPOSED_BOUNDED_REFACTORING=NONE_MANDATORY — implementation is coherent;
     optional micro-simplification only. orchestration.py size is pre-existing debt
     outside this task's scope.
EXPECTED_BENEFITS=n/a (no refactor executed or required)
RISKS=none introduced by audit
REQUIRED_TESTS=existing E1/E2/E3 suites cover the code paths (51+ outcome tests)

CODE_CHANGED=NO
```

## State after this task

```text
CRI_DEV_ENABLED=YES_PERSISTENT (survives restart + recreation)
CRI_PRODUCTION_ON=NOT_AUTHORIZED (prod mapping defaults OFF; rollout gate pending)
MCP_SPECIALISTS_LIVE=PASS (TÉO/VISTA/DAVI real tools/call from real service)
AUDIT=EXECUTED (no mandatory refactor; defects enumerated for separate decisions)
RUNTIME_CODE_CHANGED=NO (CRI code untouched; only infra compose mappings added)
MATERIAL_ACT=0
I04_ACCEPTED=NO
C3_EXECUTED=NO
```

**Lineage note:** authored against `origin/main` `2f6cb084db…`; this document's own commit SHA is recorded in the ledger, never inside the file.
