# Auditoria — classes `drawing-metrics__*`

> Data: jun/2026 · Escopo: `plugins/minha-delpi-chat`

## `drawing-metrics__status-list` e `drawing-metrics__recent`

| Ocorrência | Arquivo | Notas |
|------------|---------|--------|
| Estilos de compatibilidade | `src/ui/components/admin/shared/admin-primitives.css` | Mantidos para HTML legado eventual; equivalente a `AdminRankedList` / `AdminDataTable` |
| **Nenhum** `.tsx` de métricas | — | Fase 2 migrou para primitivos |

**Conclusão:** uso em componentes React **eliminado**. CSS legado permanece sob `.mdc-admin-root` até remoção na Fase 5.

## Outras classes `mdc-admin-drawing-metrics*`

| Arquivo | Classe | Ação |
|---------|--------|------|
| `AdminKpiCard.tsx` | `mdc-admin-drawing-metrics__grid` | Alias de grid KPI — OK |
| `AdminQualityOperations.tsx` | `mdc-admin-drawing-metrics__header` | Migrar para `AdminMetricSection` na Fase 4/5 |

## Comando de verificação

```bash
cd plugins/minha-delpi-chat
grep -Rn "drawing-metrics__status-list\|drawing-metrics__recent" src --include='*.tsx'
# esperado: sem resultados
```
