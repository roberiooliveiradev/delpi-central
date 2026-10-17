# 36 — Stage 04 · Completeness, Resolution and Minimal Dialogue

**TASK:** `DELIA-C3-STAGE03-CLOSURE-AND-STAGE04-IMPLEMENTATION-01` / TASK B  
**MODE:** bounded EXTEND — owner `entity_schemas` completeness before PREPARE  
**STATUS:** `IMPLEMENTATION_EVIDENCE_RECORDED` · `STAGE_04_ACCEPTED=NO`

---

## 1. Escopo

Identificar campos internos obrigatórios publicados pelo owner (catalog `entity_schemas`), aplicar somente defaults declarados, falhar fechado antes de PREPARE quando incompleto, e clarificar só o que falta — sem Domain validator paralelo, sem ACT por MESSAGE.

## 2. Reuse gate

```text
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND
```

Reutilizado: `_build_arguments`, `_resolve_missing_inputs`, `_clarification_question`, discovery structured, PREPARE/ACT gates, B1/B2. Sem novo planner/registry/resolver.

## 3. Alterações

`orchestration.py`:

- `_extract_owner_entity_schemas` / `_owner_entity_completeness_gaps`
- `_apply_owner_declared_defaults` (somente `defaults` publicados)
- `_argument_completeness_gaps` após projeção de argumentos e pós-resolver
- `discovery_structured` preservado do DISCOVERY outcome

## 4. Testes

- `tests/test_stage04_completeness_resolution.py` — nested helper, entity gaps, defaults, incomplete→clarify (0 ACT), complete→PREPARE pending
- CI-04/CI-10 atualizados para GREEN (clarify antes de PREPARE)
- Stage 03 iterative + discovery regression PASS
- Suíte `delia-api` pytest completa verde

## 5. Live SSH

### 5.1 First live (implementation window — §6.214)

```text
SSH_DEPLOYED_SHA=06f3b4ebdd
REAL_MODEL=moonshotai/kimi-k3
CORRELATION_ID=c4b9c803-db6f-4cce-9464-87d71bb62990
REQUEST_ID=67206e7d-3255-455b-93bb-564144ddab5d

LIVE_CAPABILITY_SELECTED=mcp:teo / prepare_record_change (PREPARE)
DISCOVERY=teo.get_catalog (ok)
ARGUMENTS=none (model invalid_structured_output)
PREPARE_INVOKE=0
MATERIAL_ACT_COUNT=0
LIVE_RESULT=EVIDENCE_RECORDED_BOUNDED
```

Completeness clarify not reached (projection failed closed).

### 5.2 Final completeness live — `DELIA-C3-STAGE04-FINAL-COMPLETENESS-LIVE-VALIDATION-01` (§6.216)

```text
SSH_DEPLOYED_SHA=1150735788
REAL_MODEL=moonshotai/kimi-k3
CORRELATION_ID=2c368fa2-fccb-4f99-bf6f-7594beeedaa3
REQUEST_ID=0d89c00d-f5cc-4ec5-9905-0cedaf7265d9
MODE=MESSAGE_ONLY

CAPABILITY_SELECTED=YES (mcp:teo / prepare_record_change)
OWNER_CATALOG_ACCESSED=YES (teo.get_catalog)
ARGUMENT_PROJECTION=PASS (decision=built missing=0)
COMPLETENESS_LOG=completeness_not_ready ABSENT (zero gaps reported)
PREPARE_INVOKE=YES → PREPARE_PROJECTED READY → CONFIRMATION_REQUIRED
CLARIFICATION_REQUIRED=NO
MATERIAL_ACT_COUNT=0
INCOMPLETE_PREPARE_INVOKED=NO
SURFACE=GROUNDED confirmation preview (nome_processo preserved; status_processo present in preview)

LIVE_VERDICT=NOT_EXERCISED
```

Owner accepted PREPARE as structurally READY with confirmation; Stage04 missing-field clarification path was not exercised (no `completeness_not_ready`, no ask-back for absent required fields). Deterministic Stage04 suite remains the evidence for gap→clarify.

## 6. Limitações / resíduos

- Completude tipada nested já coberta por `validate_arguments`; esta etapa cobre payloads opacos + `entity_schemas`.
- Resolver same-owner / ambiguidade / invented-id: comportamentos pré-existentes preservados; não reescritos.
- Final live: projection PASS + PREPARE READY; completeness **clarify** path `NOT_EXERCISED` (model-supplied args satisfied gate with 0 gaps).
- Live proof of minimal clarification for missing owner-required fields still absent.
- `STAGE_04_ACCEPTED=NO` até review independente.
- `C3_EXECUTED=NO`; `C4_AUTHORIZED=NO`.

## 7. NEXT

```text
NEXT=INDEPENDENT_STAGE04_ACCEPTANCE_REVIEW
```
