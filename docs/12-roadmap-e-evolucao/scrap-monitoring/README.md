# Scrap Monitoring (Acompanhamento de Refugos)

Plugin id técnico: **`scrap-monitoring`**. Nome exibido ao usuário: **Acompanhamento de Refugos**.

Scaffold do plugin MFE multi-filial (SC/ES) + API `/refugos` (jul/2026).

## Status

| Fase | Entrega | Status |
|------|---------|--------|
| API | `/refugos/*` (resumo, rankings, registros, filtros, health) | feito |
| RBAC | `.view.filial-sc` / `.view.filial-es` + gate 403 | feito |
| Plugin scaffold | Manifest SC/ES + stub UI | feito |
| UI completa | KPIs / gráficos / tabela | backlog |

## Filiais

| Rota UI | Código TOTVS |
|---------|--------------|
| `/apps/scrap-monitoring/sc` | `01` |
| `/apps/scrap-monitoring/es` | `02` |

## Docs

- [API](../../../api-delpi/docs/api/scrap-monitoring.md)
- [Plugin README](../../../plugins/scrap-monitoring/README.md)
