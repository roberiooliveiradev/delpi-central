# Smoke SIPOC — validação do orçamento conversacional

**TASK:** `DELIA-C3-I04-SIPOC-REAL-MODEL-BUDGET-VALIDATION-01`  
**DATA:** 2026-10-20  
**SOURCE_HEAD:** `e7d58aee98eed346c741c6d665d9746469b22fcd`  
**FIX_SHA:** `a9f5f8d3c2ac389747ce4249e0e185cca72f52e1` (ancestral do source)

## Runtime

```text
HOST_GIT=e7d58aee98eed346c741c6d665d9746469b22fcd
FIX_IN_HOST_GIT=YES
IMAGE_CREATED=2026-10-20T16:45:32Z
CONTAINER_STARTED=2026-10-20T16:45:32Z
EARLY_CONVERSATIONAL_ADMISSION_IN_PROCESS=NO
HANDLER_USES_MARKER=NO
CONVERSATIONAL_FALLBACK_CAP_SECONDS=12
GLOBAL_BUDGET_SECONDS=30
MODEL_ID=moonshotai/kimi-k3
```

O checkout do host contém a correção. O processo `delpi-delia-api` não. A imagem foi criada às 16:45:32Z, antes do commit do marcador. `hasattr(EARLY_CONVERSATIONAL_ADMISSION)` no processo retornou falso.

## Execução

Não houve pergunta. O plano 16 e o ledger §6.337 registram `PRODUCTION_DEPLOY_AUTHORIZED=NO`. Este pedido não autoriza deploy. Testar o container atual atribuiria o resultado à versão sem a correção.

```text
TASK_OUTCOME=TEST_NOT_RUN
BLOCKED=DEPLOY_NOT_AUTHORIZED
SIPOC_BUDGET_FIX=INCONCLUSIVE
REAL_MODEL_QUESTIONS=0
MATERIAL_ACT=0
Q03_AUTHORIZED=NO
```
