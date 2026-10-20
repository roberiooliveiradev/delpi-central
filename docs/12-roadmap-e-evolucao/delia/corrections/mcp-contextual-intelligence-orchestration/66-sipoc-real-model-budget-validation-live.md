# Smoke SIPOC — pergunta real após o script de deploy

**TASK:** `DELIA-C3-I04-SIPOC-REAL-MODEL-BUDGET-VALIDATION-01`  
**DATA:** 2026-10-20  
**FIX_SHA:** `a9f5f8d3c2ac389747ce4249e0e185cca72f52e1`

## Deploy

O pedido autorizou o procedimento canônico. No host:

```text
PROCEDURE=./infra/scripts/up-prod-sequential.sh --pull --build delia-api
SCRIPT_EXIT=0
GIT_PULL=already up to date
HOST_HEAD=a9c3df812dfcea13e7a27b46d5b1015edc58afea
BUILD=COPY delia-api em cache
CONTAINER=delpi-delia-api já em execução
CONTAINER_STARTED=2026-10-20T17:18:18Z
IMAGE=sha256:a1fe196c994b
```

O script não recriou o container porque a imagem já correspondia ao checkout que contém a correção. A pergunta rodou nesse processo, não numa imagem anterior.

## Processo verificado antes da pergunta

```text
EARLY_CONVERSATIONAL_ADMISSION=early_conversational_admission
HANDLER_USES_MARKER=YES
ORCHESTRATION_SETS_ADMISSION_OUTCOME=YES
CONVERSATIONAL_FALLBACK_CAP_SECONDS=12
GLOBAL_BUDGET_SECONDS=30
MODEL_ID=moonshotai/kimi-k3
```

O valor 12 permanece no código para o fallback pós-orquestração. A admissão antecipada não usa esse teto.

## Pergunta única

Texto: «O que é SIPOC?». Comando `MESSAGE`. Sem retry. Sem ACT.

```text
HTTP_STATUS=200
ADMISSION_OUTCOME=conversational
ADMISSION_LATENCY_MS=2289
TOTAL_LATENCY_MS=13412
ANSWER_STAGE_MS=11123
MODEL_PROPOSE_OK=1
MODEL_INVOCATION_PRESENT=YES
MODEL_CALL_COUNT=2
SELECTED_OWNER=none
SELECTED_CAPABILITY=none
CONFIRMATION=absent
GROUNDING_STATUS=NON_GROUNDED
EPISTEMIC_CLASS=HYPOTHESIS
TERMINATION_REASON=completed
BUDGET_PHRASE=absent
LIMITATIONS=conceito geral; sem verificação de SIPOC em registros DELPI
```

A resposta cobre Suppliers, Inputs, Process, Outputs e Customers, com o papel de cada elemento, e declara que não consultou registros da DELPI. Não houve seleção de owner, escrita, PREPARE ou ACT.

A etapa de resposta terminou em cerca de 11,1 s. Esta amostra, sozinha, não mostra um estágio ultrapassando 12 s. O que a distingue do encerramento anterior é o processo com o marcador, a ausência de `turn_budget_limited` e a explicação completa dentro dos 30 s.

```text
TASK_OUTCOME=PASS
SIPOC_BUDGET_FIX=PASS
MATERIAL_ACT=0
CODE_CHANGED=NO
Q03_AUTHORIZED=NO
```
