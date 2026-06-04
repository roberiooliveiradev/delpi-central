# Auditoria — classes `drawing-metrics__*`

> Data: jun/2026 · Escopo: `plugins/minha-delpi-chat`

## `drawing-metrics__status-list` e `drawing-metrics__recent`

| Ocorrência | Arquivo | Notas |
|------------|---------|--------|
| Estilos de compatibilidade | `src/ui/components/admin/shared/admin-primitives.css` | Mantidos para HTML legado eventual; equivalente a `AdminRankedList` / `AdminDataTable` |
| **Nenhum** `.tsx` de métricas | — | Fase 2 migrou para primitivos |

**Conclusão:** uso em componentes React **eliminado**. Seletores CSS `__status-list` e `__recent` **removidos** de `admin-primitives.css` na Fase 5.

## Classes `mdc-admin-drawing-metrics` restantes

| Arquivo | Uso | Notas |
|---------|-----|--------|
| `AdminMetricsTab.css` | Layout de blocos legados na aba métricas | Pode migrar para `AdminMetricSection` em refactor futuro |
| `AdminDrawingAnalysisMetrics.tsx` | `id` do título apenas | Componente já usa `AdminMetricSection` |

`AdminKpiGrid` não usa mais alias `mdc-admin-drawing-metrics__grid`.

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
