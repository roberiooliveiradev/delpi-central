# CSS — apresentação rica no chat

> Complementa [`frontend-refactor-roadmap.md`](./frontend-refactor-roadmap.md) (PR-17, tarefa C5).

## Camadas

```text
rich-presentation-shared.css     ← canônico (shell + chrome transversal + botões) — em presentation/
├── presentation/ChatRichTable.css            ← células, sort, scroll desktop, card mode mobile
├── presentation/ChatRichChart.css            ← Recharts, heatmap, toolbar UX de gráfico
├── presentation/ChatRichKpi.css              ← grid de cards KPI, trend
├── presentation/ChatRichTree.css             ← nós hierárquicos, indentação
├── presentation/ChatRichDashboard.css        ← layout de painéis empilhados
└── ChatActionResults.css        ← cards legados de tool result
```

Imports legados em `components/ChatRich*.tsx` e `rich-presentation-shared.css` reexportam de `presentation/` (PR-18).

`ChatAssistantContent.tsx` importa **somente** `rich-presentation-shared.css` para heading, insight, navegação e coverage — não depende de `ChatRichChart.css`.

## O que fica em `rich-presentation-shared.css`

| Bloco | Classes | Consumidores |
|-------|---------|--------------|
| Shell card | `.mdc-rich-table`, `.mdc-rich-chart` | Table, Chart, Tree (parcial) |
| Header/título | `__header`, `__title`, `__actions` | Table, Chart |
| Botões toolbar | `__btn`, `__toggle-btn`, copy/export | Table, Chart, KPI, Tree |
| Animação entrada | `.mdc-rich-presentation--enter` | AssistantContent |
| Chrome transversal | `.mdc-rich-presentation__*` | AssistantContentChrome, format toolbar, coverage |

## O que fica no CSS do componente

| Componente | Específico (não mover para shared) |
|------------|-------------------------------------|
| **ChatRichTable** | `__scroll`, `__table`, sort, sticky thead, footer, **card mode mobile** (`data-label`) |
| **ChatRichChart** | Recharts, heatmap, type toggle, UX fields (select/checkbox), explanation |
| **ChatRichKpi** | `__grid`, `__card`, trend colors, responsive columns |
| **ChatRichTree** | indentação, conectores, nós expandíveis |

## Mobile — tabelas (E4)

Em `≤768px`, `ChatRichTable` usa **card mode** (padrão `DataTable` do portal):

- `thead` oculto
- cada `<tr>` vira card com borda/sombra
- cada `<td>` usa `data-label={col.label}` + `::before` para rótulo da coluna
- scroll horizontal desativado no mobile (substituído por cards empilhados)

Desktop mantém tabela clássica com scroll horizontal/vertical em `.mdc-rich-table__scroll`.

## Regra para novos estilos

1. Superfície, header ou botão igual em **2+** widgets rich → `rich-presentation-shared.css`.
2. Layout ou interação exclusiva de um widget → CSS co-localizado do componente.
3. Tokens `--mdc-*` sempre; sem hex para superfície/texto.
4. Novo bloco de apresentação transversal (ex.: banner de aviso) → classe `mdc-rich-presentation__*` no shared.
