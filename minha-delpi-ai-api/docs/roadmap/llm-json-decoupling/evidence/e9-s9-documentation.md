# E9.S9 — Documentação e encerramento parcial

**Status:** `ATENDIDO_PARCIAL` (2026-09-10) — docs canônicas atualizadas; iniciativa **não** encerrada  
**Onda:** H (plano 09)

## Feito

1. Ponte em `docs/architecture/chat-intelligence-base.md` §15 + referências → ledger E9.
2. Seção `# 21` em `docs/testing/chat-ai-flow-families.md` (corpus/gates/verify-final).
3. Ledger/plano 09/README/roadmap alinhados ao estado real.

## Não feito (débito explícito)

| Débito | Motivo |
|--------|--------|
| Aceite final da iniciativa | `globalReleasePass=false` (E9.S8) |
| DELETE markers/terms/strategies | `deleteAuthorized=false` (E9.S6) |
| Live unknown API / send-stream / eficiência | dims INCONCLUSIVE |
| Remover pasta roadmap | ainda tem valor (débitos + gates) |

## Aceite final (plano) — estado

```text
GENERALIZATION = PASS_OFFLINE (live INCONCLUSIVE)
SAFETY = PASS_OFFLINE
OUTCOME = PASS_OFFLINE
EFFICIENCY = INCONCLUSIVE
LEGACY_CATALOG_AUTHORITY = CUTOVER_ON / DELETE_PENDING
TECHNICAL_JSON_DUPLICATION = JUSTIFIED_OR_PENDING_DELETE (E9.S7)
MANUAL_NLU_RULES = REDUCED_PARTIAL (shadow/cutover)
DOCS_CANONICAL = UPDATED (esta fatia)
```

## Próximo (fora de “fechar falso”)

1. Live L1–L4 / trials LLM para dims INCONCLUSIVE.
2. Reavaliar E9.S6 → `deleteAuthorized=true` quando gates plenos.
3. Executar DELETEs classificados em E9.S7 `REMOVE_WHEN_GATES_PASS`.
4. Re-rodar E9.S8 até `globalReleasePass=true`.
5. Só então encerrar roadmap ou arquivar.
