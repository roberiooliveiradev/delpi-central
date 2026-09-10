# E1.S4 — Agree-rate aggregation (admin)

**Status:** `AGREE_AGG_ON` (2026-09-10) — ainda **não** é cutover de seleção  
**Onda:** B (plano 01)

## O que entrou

| Peça | Path |
|------|------|
| Snapshot audit | `registrySelectionShadows[]` em `ai_audit_logs.metadata` via `ChatTurnCompletionAuditService` |
| Propagação | `selectedExternalAction` copia shadow do planned tool (`chat_tool_context_selection_service`) |
| Aggregate | `RegistrySelectionShadowObservabilityService.aggregate_snapshots` |
| Admin API | `GET /admin/metrics/registry-selection-shadow/summary?hours=` |
| Docs | `docs/api/08-admin.md` |

## Contrato do summary

```json
{
  "samplesCount": 0,
  "agreeCount": 0,
  "divergeCount": 0,
  "agreeRate": null,
  "byKind": {},
  "divergeRecent": [],
  "recent": [],
  "cutoverReadyHint": "not_ready | candidate | investigate_divergences"
}
```

`cutoverReadyHint`:
- `not_ready` se `samplesCount < 20`
- `candidate` se `agreeRate >= 0.95`
- `investigate_divergences` caso contrário

## Aceite desta fatia

```text
AUDIT_SNAPSHOT_WIRED = PASS
ADMIN_SUMMARY_ENDPOINT = PASS
AGGREGATE_AGREE_RATE = PASS
SELECTION_AUTHORITY_UNCHANGED = PASS
CUTOVER_DEFAULT_CANDIDATE = NOT_STARTED
```

## Próximo

1. Coletar janela live (`hours=168`) até `samplesCount` e `agreeRate` estáveis.  
2. Revisar `divergeRecent` (explicáveis vs bugs).  
3. Só então cutover de seleção (E1.S6 fatia B) — ainda bloqueado pelo ledger sem unknown/metamorphic.
