# Playbook 09 — Apresentação Rica

Projeto: Minha DELPI Chat IA  
Escopo: tabelas, gráficos, KPIs, árvores, cards, checklists, lousa, dashboards e escolha automática do melhor formato de resposta.

> **Princípio:** Dado certo no formato certo. Implementação no **chat base** (presenter + MFE), sem duplicar em agentes.

Legado: [`apresentacao-rica-chat-onda-9.md`](./apresentacao-rica-chat-onda-9.md), [`melhorias/playbook_ampliacao_graficos_minha_delpi_chat.md`](./melhorias/playbook_ampliacao_graficos_minha_delpi_chat.md), [`melhorias/playbooks_melhoria_minha_delpi_chat/09_dashboards_graficos_apresentacao_rica.md`](./melhorias/playbooks_melhoria_minha_delpi_chat/09_dashboards_graficos_apresentacao_rica.md).

---

## Implementação (jun/2026)

| Componente | Responsabilidade |
|------------|------------------|
| `ChatPresentationDataShapeAnalyzer` | Linhas/colunas, data, numérico, hierarquia, recomendação interna |
| `ChatPresentationDecisionService` | Formato preferido, fallback, `availableViews`, motivo |
| `ChatChartTypeSelectionService` | Subtipo de gráfico (linha, barra H, rosca, combo, …) |
| `ExternalActionResultPresenter` | Monta `presentation` / `tablePresentation` / `chartPresentation` |
| `ExecuteExternalActionUseCase` | Enriquece metadata com `presentationDecision` |
| MFE `ChatRichPresentation` | Renderização, toggle texto/tabela/gráfico/árvore, export |

---

## Pipeline

```
Dados da action → Presenter (table/chart/tree/kpi)
               → ExecuteExternalActionUseCase (primary + availableFormats)
               → ChatPresentationDecisionService.enrich_metadata
               → metadata.presentationDecision + preferredFormat
               → MFE ChatRichPresentation
```

---

## Metadata `presentationDecision` (exemplo)

```json
{
  "presentationDecision": {
    "selected": "line_chart",
    "fallback": "table",
    "reason": "dados temporais com valor numérico",
    "availableViews": ["line_chart", "table", "chart"],
    "dataShape": {
      "rows": 12,
      "columns": 2,
      "hasDate": true,
      "hasNumeric": true,
      "hasCategory": true,
      "hasHierarchy": false
    },
    "intent": "sales_lookup"
  }
}
```

---

## Testes de regressão

| Caso | Dados / pedido | Formato esperado |
|------|----------------|------------------|
| P1 | Lista simples | `table` |
| P2 | Data + valor | `line_chart` |
| P3 | Ranking (nomes longos) | `horizontal_bar` |
| P4 | Participação | `donut` |
| P5 | Indicador único | `kpi` |
| P6 | BOM / hierarquia | `tree` |
| P7 | Texto longo / lousa | `canvas` |
| P8 | Pendências | `checklist` |
| P9 | Muitas categorias | `horizontal_bar` |
| P10 | Sem número | `table` |
| P11 | Meta x realizado | `grouped_bar` |
| P12 | Pedido de gráfico | `chart` |
| P13 | Pedido de tabela | `table` |
| P14 | Dados vazios | `text` |
| P15 | Formato pedido (linha) | `line_chart` |

Arquivos: `tests/fixtures/rich_presentation_cases.py`, `tests/unit/domain/services/test_rich_presentation.py`.

---

## Roadmap

| Fase | Status |
|------|--------|
| 1 — Decisão básica de formato | **Concluída** — API + MFE (`presentationDecision`, insight, toggle inicial, chips de alternância) |
| 2 — Gráficos ampliados | Parcial (Onda 9 + `ChatChartTypeSelectionService`) |
| 3 — Alternância de visualização | Parcial (MFE toggle, refinamento de formato) |
| 4 — Interatividade | Parcial (drill-down, menus de linha/nó) |
| 5 — Dashboards e insights | Parcial (`ChatDashboardPresentationService`) |
| 6 — Métricas e otimização | Backlog (feedback por formato, admin) |

---

## Resumo executivo

Apresentação rica transforma dados em entendimento. O Playbook 09 consolida a escolha automática de formato no chat base; fases 2–6 evoluem sobre a base da Onda 9 sem reimplementar o MFE.
