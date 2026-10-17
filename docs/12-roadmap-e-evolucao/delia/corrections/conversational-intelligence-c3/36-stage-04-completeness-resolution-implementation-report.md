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

```text
SSH_DEPLOYED_SHA=06f3b4ebdd
REAL_MODEL=moonshotai/kimi-k3 (runtime default)
CORRELATION_ID=c4b9c803-db6f-4cce-9464-87d71bb62990
REQUEST_ID=67206e7d-3255-455b-93bb-564144ddab5d

LIVE_CAPABILITY_SELECTED=mcp:teo / prepare_record_change (PREPARE)
DISCOVERY=teo.get_catalog (ok)
ARGUMENTS=none (model invalid_structured_output; missing=0 reported)
PREPARE_INVOKE=0
MATERIAL_ACT_COUNT=0
INVENTED_IDENTIFIERS=0
HAS_CONFIRMATION=false
GROUNDING_STATUS=NON_GROUNDED (surface content; orchestration selected capability)
PREPARE_STATE=NOT_READY
CLARIFICATION_RELEVANT=NO (projection failed before completeness clarify)
LIVE_RESULT=EVIDENCE_RECORDED_BOUNDED
```

MESSAGE-only; zero ACT. Completeness gate not exercised on this live turn because argument projection failed closed before PREPARE — covered by deterministic Stage04 suite.

## 6. Limitações / resíduos

- Completude tipada nested já coberta por `validate_arguments`; esta etapa cobre payloads opacos + `entity_schemas`.
- Resolver same-owner / ambiguidade / invented-id: comportamentos pré-existentes preservados; não reescritos.
- Live: seleção PREPARE + discovery ok; args projection `invalid_structured_output` → sem clarificação Stage04 nesta turn.
- Live real de gaps `entity_schemas` ainda depende de args válidos + catalog estruturado.
- `STAGE_04_ACCEPTED=NO` até review independente.
- `C3_EXECUTED=NO`; `C4_AUTHORIZED=NO`.

## 7. NEXT

```text
NEXT=INDEPENDENT_STAGE04_ARCHITECTURE_REVIEW
```
