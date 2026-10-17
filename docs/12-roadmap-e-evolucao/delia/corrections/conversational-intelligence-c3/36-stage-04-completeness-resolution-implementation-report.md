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

Registrado no ledger §6.214 após deploy do SHA desta implementação (MESSAGE-only; zero ACT).

## 6. Limitações / resíduos

- Completude tipada nested já coberta por `validate_arguments`; esta etapa cobre payloads opacos + `entity_schemas`.
- Resolver same-owner / ambiguidade / invented-id: comportamentos pré-existentes preservados; não reescritos.
- Live real depende de catalog owner publicar `entity_schemas` estruturado.
- `STAGE_04_ACCEPTED=NO` até review independente.
- `C3_EXECUTED=NO`; `C4_AUTHORIZED=NO`.

## 7. NEXT

```text
NEXT=INDEPENDENT_STAGE04_ARCHITECTURE_REVIEW
```
