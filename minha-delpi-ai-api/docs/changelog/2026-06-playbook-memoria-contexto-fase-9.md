# Changelog — Playbook memória e contexto (Fase 9)

**Data:** 03/06/2026

## Métricas e feedback

- `ChatSessionMemoryAdminMetricsService`: snapshot em auditoria, agregação de uso e feedback `memory_*`.
- `ChatMemoryContextLossAlertService`: `memoryContextAlerts` quando assertividade ou ambiguidade indicam risco.
- `GET /admin/metrics/session-memory/summary?hours=168`
- MFE: `AdminSessionMemoryMetrics` na aba Métricas.
- Feedback: `memoryAssertivenessScore` no contexto técnico; `lost_context` inclui motivos `memory_*`.

## Validação

```bash
./scripts/run_memory_context_validation.sh
cd plugins/minha-delpi-chat && npm run build
```
