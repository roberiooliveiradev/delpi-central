# 32 — Stage 03 · Discovery Relevance Fix (RW-S03-01)

**TASK:** `DELIA-C3-STAGE03-DISCOVERY-RELEVANCE-FIX-01`  
**MODE:** minimal EXTEND of existing vocabulary gate — no Stage 03 reimplementation  
**BASE_HEAD:** `c193d49f76` (contains implementation ref `e3104a1690`)  
**STATUS:** `FIX_EVIDENCE_RECORDED` · `STAGE_03_ACCEPTED=NO`

---

## 1. Finding

`RW-S03-01`: `_requires_owner_vocabulary()` treated any required string without `enum`/`const` as needing DISCOVERY. Legitimate free text (`search_query`, `description`, names) could force unrelated catalog calls.

## 2. Root cause

Stage 03 EXTEND conflated “open string” with “owner-controlled vocabulary”. JSON Schema free strings cannot deterministically express catalog membership without `enum`/`const` or an opaque envelope.

## 3. Fix

File: `delia-api/app/application/capability_provision/orchestration.py`

- `_requires_owner_vocabulary` again relies **only** on `_is_open_vocabulary` (opaque object/array envelopes).
- Required free strings alone never trigger DISCOVERY.
- `_is_unconstrained_string` retained as a structural helper (documents open text; does not drive discovery).

No new metadata, planner, registry, wire fields, or frontend.

## 4. Limit (explicit)

Without owner-declared `enum`/`const` or opaque envelope, DÉLIA does **not** speculate DISCOVERY for free-text fields. Controlled-topic guidance must publish vocabulary via those existing contracts.

## 5. Tests

`tests/test_stage03_discovery_guidance.py` (+ baseline CI-01 expectation restore):

| Scenario | Result |
|---|---|
| Required `search_query` + unrelated DISCOVERY | no catalog call |
| Required `description` + DISCOVERY peer | no catalog call |
| Opaque-envelope guidance | DISCOVERY → grounded READ preserved |
| Closed enum | no unnecessary DISCOVERY |
| Opaque envelope PREPARE path (provider-neutral suite) | preserved |
| Tool/owner rename | same envelope behavior |
| Writing-verb guidance question | zero PREPARE/ACT |

## 6. Outcome

```text
RW_S03_01_STATUS=FIXED
FREE_TEXT_FALSE_DISCOVERY=PASS
VALID_GUIDANCE_PRESERVED=PASS (opaque-envelope contract)
OPAQUE_ENVELOPE_PRESERVED=PASS
STAGE_03_ACCEPTED=NO
MATERIAL_ACT_COUNT=0
NEXT=INDEPENDENT_STAGE03_REVIEW
```

Doc 31 left unchanged (historical implementation evidence).
