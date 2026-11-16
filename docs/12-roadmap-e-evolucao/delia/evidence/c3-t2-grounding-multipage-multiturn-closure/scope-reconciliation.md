# Reconciliação de escopo — commits e verificação

## Ancestralidade

```text
c78d4a51d9  (parent do commit funcional)
    └── c0891eb1a5  fix(delia): coerência G2 grounding, multipágina e recovery multi-turno
          └── e327b08e5a  docs(ui-review)          ← FORA DÉLIA
                └── 9488209013  test(my-requests) ← FORA DÉLIA
                      └── 550eae558d  fix(delia): clarificação residual só cede a obrigações SATISFIED
```

## Matriz de arquivos

| Arquivo | Commit de origem | Owner | Escopo DÉLIA | Verificação anterior | Verificação atual |
|---|---|---|---|---|---|
| `delia-api/app/application/capability_provision/semantic_capability_support.py` | `c0891eb1` + `550eae55` | delia-api application | YES | R1 WT + R3 só OC-1 | Completo (funcional+OC1+novos) |
| `delia-api/app/infrastructure/orchestration/pydantic_ai_investigation.py` | `c0891eb1` | delia-api infrastructure | YES | R1 WT (omitido no range R3) | Completo |
| `delia-api/scripts/int1_openrouter_qwen14b_instrumented_eval.py` | `c0891eb1` | delia-api scripts | YES | R1 WT | Completo |
| `delia-api/tests/test_int1_investigative_progress_rework.py` | `c0891eb1` | delia-api tests | YES | R1 WT | Completo |
| `delia-api/tests/test_r6_invented_identifier_rejection.py` | `c0891eb1` | delia-api tests | YES | R1 WT | Completo |
| `delia-api/tests/test_two_agent_experiment.py` | `c0891eb1` | delia-api tests | YES | R1 WT | Completo |
| `docs/.../16-execution-master-plan.md` | `c0891eb1` | delia docs | YES | R1 WT | Completo |
| `docs/.../20-testing-and-acceptance-matrix.md` | `c0891eb1` | delia docs | YES | R1 WT | Completo |
| `docs/.../293-c3-four-gate-...md` | `c0891eb1` | delia docs | YES | R1 WT | Completo |
| `docs/.../engineering-closure-residual-register.md` | `c0891eb1` | delia docs | YES | R1 WT | Completo |
| `docs/.../execution-ledger.md` | `c0891eb1` | delia docs | YES | R1 WT | Completo |
| `docs/.../evidence/c3-t2-grounding-multipage-multiturn-closure/**` | esta task | delia evidence | YES | N/A | Esta verificação |
| `delia-api/tests/test_c3_t2_evidence_closure_negatives.py` | esta task | delia-api tests | YES | N/A | Esta verificação |
| arquivos my-requests / ui-review / CF WIP | commits intercalados / WT | outros | NO | Excluídos do commit DÉLIA | Excluídos |

## Lacuna da verificação R3 anterior

O range `c0891eb1..550eae55` inclui commits concorrentes e **não** contém o
diff funcional de `c0891eb1` (só o delta OC-1 + intercalados). Esta task
reabre verificação sobre o **conjunto funcional completo** (blobs dos dois
commits DÉLIA + novos artefatos/testes), sem atribuir my-requests/ui-review
à DÉLIA.
