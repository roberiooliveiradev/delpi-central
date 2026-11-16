# Testes e CI — evidence closure

**BASE_SHA (task start):** `f77e580f0ddfec488bf757a1298e2b5e86dc5425`  
**Functional:** `c0891eb1a5` · **OC-1:** `550eae55`

## Comandos locais (container `delpi-delia-api`, código montado)

| COMMAND | WORKDIR | EXIT | Notas |
|---|---|---|---|
| `pytest -q` suites G2/R5/R6/REF05/negatives/native-first | `/app` | `0` | ver `logs/pytest-targeted.txt` |
| `pytest -q` int2/g1/delivery + comprehension/int3/authz | `/app` | `0` | `logs/pytest-regression-related.txt` + `pytest-extra.txt` |
| `pytest -q tests/ --ignore=live --ignore=e2e` | `/app` | `0` | `logs/pytest-full-delia.txt` / meta |
| `python -m unittest scripts/ci/test_audit_architecture_phase3.py -v` | repo | `0` | `logs/audit-phase3.txt` |
| `python -m unittest scripts/ci/test_audit_platform_guardrails.py -v` | repo | `0` | `logs/audit-guardrails.txt` |
| `audit_architecture_phase3.py --check --base c0891eb1a5^` | repo | `0` | `logs/audit-phase3-check.txt` |
| `audit_platform_guardrails.py --check --base c0891eb1a5^` | repo | `0` | `logs/audit-guardrails-check.txt` |

## CI remoto (commits de referência já publicados)

| SHA | Workflow | RUN | CONCLUSION |
|---|---|---|---|
| `c0891eb1a5` | Architecture Enforcement | [43775973780](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43775973780) | `success` |
| `c0891eb1a5` | Cursor Rules Governance | [43775973777](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43775973777) | `success` |
| `550eae558d` | Architecture Enforcement | [43776667191](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43776667191) | `success` |

Não existe workflow CI dedicado à suíte pytest da `delia-api` no push de `main`.
O gate canônico aplicável ao diff Python é `architecture-enforcement.yml`
(reproduzido localmente com EXIT=0). Após o push desta task, os check-runs
do SHA final devem ser conferidos na API pública do GitHub.

## Autoridade do gate local equivalente

- `.cursor/rules/test-and-commit.mdc` — comandos de enforcement transversal
- `.github/workflows/architecture-enforcement.yml` — jobs `architecture-gate`
- CI remoto dos commits funcionais/OC-1 já `success` (links acima)

## Segurança de publicação

- `DELIA_TWO_AGENT_EXPERIMENT` default `False` + fail-closed em produção
- Push **não** dispara deploy automático da DÉLIA; deploy em `srv-api` exige
  passo explícito `up-prod-sequential.sh` (vetado nesta fase)
- `PRODUCTION_DEPLOY=NOT_AUTHORIZED`
FULL_SUITE_COLLECT: 
FULL_SUITE_EXIT: 0
NEGATIVES_FILE_TESTS: 17
