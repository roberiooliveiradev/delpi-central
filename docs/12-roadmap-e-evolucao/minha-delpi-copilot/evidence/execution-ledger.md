# Minha DELPI Copilot — Execution Ledger

**Status do programa:** `PLANNED / NOT_STARTED`  
**Plano ativo:** [`../16-execution-master-plan.md`](../16-execution-master-plan.md)  
**Protocolo:** [`../22-cursor-execution-protocol.md`](../22-cursor-execution-protocol.md)  
**Próxima etapa obrigatória:** **C0.S0 — Rebaseline e inventário real**

## 1. Regra do ledger

Este arquivo registra o estado executável vigente. Não apagar histórico; adicionar eventos e atualizar a tabela de status quando evidence justificar.

Uma etapa só muda para `PASS` quando `COMPLETE_GATE=PASS` no HEAD correspondente.

## 2. Status por fase

| Fase | Status | Etapa atual | Dependência/bloqueio |
|---|---|---|---|
| C0 Fundação/inventário | **NOT_STARTED** | **C0.S0** | nenhuma; iniciar aqui |
| C1 Platform Actions | LOCKED | — | C0 completo |
| C2 Workspace Context | LOCKED | — | C1 base + contratos C0 |
| C3 Business Action Parity | LOCKED | — | C2 + gates AI/OpenAPI-first relevantes |
| C4 Agentic Workflows | LOCKED | — | C3 |
| C5 Ecossistema AI-ready | LOCKED | — | C3/C4 foundation |
| C6 Autonomia governada | LOCKED | — | C4/C5 + safety gates |
| C7 Rollout final | LOCKED | — | C0–C6 required gates |

## 3. Dependência externa vigente

A iniciativa `minha-delpi-ai-api/docs/roadmap/llm-json-decoupling/` está documentada com `VERIFY_FINAL_FAILED` após auditoria pós-fechamento.

Classificação para o Copilot:

```text
C0-C2 = podem avançar
C3 scaffolding/tests = pode avançar se não mascarar dependência
C3 production-ready Business Actions = BLOCKED até gates relevantes PASS
C4+ production workflows com Business Actions = BLOCKED pela mesma dependência
```

O Copilot não assume ownership da correção da Onda J.

## 4. Registro de execução

| Data | HEAD | Etapa | Evento | Status/evidence |
|---|---|---|---|---|
| 2026-09-12 | `TO_CAPTURE_AT_C0.S0` | Planejamento | documentação arquitetural/funcional e plano executável criados | PLAN_ONLY |

## 5. Template de evento

```text
DATE:
STEP:
HEAD_BEFORE:
HEAD_AFTER:
STATUS:
EVIDENCE:
TESTS:
COMPLETE_GATE:
NEXT_UNLOCKED:
NOTES:
```

## 6. Estados permitidos

```text
NOT_STARTED
READY_TO_EXECUTE
IN_PROGRESS
BLOCKED_WITH_EVIDENCE
EXECUTION_DRIFT
FAIL
PASS
LOCKED
```

Evitar aliases vagos como “quase pronto”, “feito com ressalva” ou “100% salvo X”.

## 7. COMPLETE_GATE

Bloqueantes de PASS quando materiais ao step:

```text
PARTIAL
INCONCLUSIVE
PENDING
LEGACY_FALLBACK
SHADOW_ONLY sem exit criteria
TODO/FIXME/HACK/TEMPORARY
TEST_NOT_RUN
STALE_EVIDENCE
```

## 8. Primeiro comando de execução

O Cursor deve abrir [`../23-prompt-cursor-execucao.md`](../23-prompt-cursor-execucao.md) e iniciar **C0.S0**, sem runtime diff antes de concluir o inventário.