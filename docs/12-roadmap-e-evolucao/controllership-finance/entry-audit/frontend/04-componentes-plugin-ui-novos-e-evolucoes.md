# Entry audit · Front-end 04 — Componentes novos e evoluções no `@delpi/plugin-ui`

| Campo | Valor |
|---|---|
| Status | **DESIGN_DRAFT** |
| Data | 2026-11-13 |
| Nota | O filtro de período usa dois `DateField` (De/Até) que já existem: período livre, sem atalhos, como na skill (decisão do owner, 2026-11-13). Por isso não há componente novo de período. |
| Usado por | páginas [01](./01-pagina-entrada-e-execucao.md), [02](./02-pagina-dashboard-da-analise.md), [03](./03-pagina-detalhe-da-ocorrencia.md) |
| Baseline | `@delpi/plugin-ui` no HEAD `08825074` |

## Regras para todos

- Nascem e evoluem **no `@delpi/plugin-ui`**, nunca no MFE. O Portal importa por adapter `Cf*` (doc 00).
- **Genéricos:** nada de «auditoria», «NF», «Protheus», «fornecedor» no nome, nas props ou nos textos padrão. Textos padrão em PT-BR, todos substituíveis por `labels`.
- Seguem o padrão do kit: `prefix` (BEM, padrão `ds`/`delpi-ui`), `classNames` parcial com `…BemClasses(prefix)`, `className`, tokens de tema (claro/escuro na mesma árvore), sem cor fixa.
- **Evolução é aditiva:** props novas opcionais; sem elas, o componente se comporta e renderiza exatamente como hoje. Antes de mudar, testes de caracterização do comportamento atual (mesmo padrão usado na evolução do `RealtimeSocketClient`, W2b da frente 167).
- Cada componente: testes de unidade e de render (teclado, ARIA, claro/escuro), demo no catálogo (`catalog/demos/*.tsx`), export no índice da pasta e no `index.ts` do pacote, tipos exportados, linha no [mapa de reuso 30](../../30-plugin-ui-reuse-map.md) (PLANNED → PROVEN).
- Regressão: suíte do plugin-ui e build/typecheck de todos os consumidores que importam o componente evoluído.

## Resumo

| § | Componente | Tipo | Pasta | Onde é usado |
|---|---|---|---|---|
| 1 | `DistributionDonut` | **novo** | `components/charts/` | P02 (temas) |
| 2 | `ResolutionStatusCell` | **novo** | `components/data/` | P02 (tabelas), P03 (rodapé) |
| 3 | `ScopeChipBar` | evoluir | `components/feedback/` | P02 (filtros ativos) |
| 4 | `SemicircleProgressGauge` | evoluir | `components/charts/` | P02 (conformidade) |
| 5 | `HorizontalValueBars` | evoluir | `components/charts/` | P02 (fornecedores, severidade, TES) |
| 6 | `ComparativeAreaChart` | evoluir | `components/charts/` | P02 (por dia) |

---

## 1. `DistributionDonut` — novo

Rosca de distribuição com lista ao lado, em que cada fatia e cada item da lista filtram. Hoje a rosca existe só dentro do `ConfigurableSeriesChart` (`chartType="pie"`, `pieInnerRadiusRatio`), cuja `interaction` é de edição, não de seleção. O novo componente reaproveita o desenho de `ChartSeriesPie` (sem duplicar o cálculo dos arcos) e acrescenta seleção.

### Props

```ts
export type DistributionDonutTone =
  | "chart-1" | "chart-2" | "chart-3" | "chart-4" | "chart-5" | "chart-6" | "chart-7" | "chart-8"
  | "success" | "warning" | "danger" | "info" | "neutral";

export type DistributionDonutItem = {
  id: string;
  label: string;
  value: number;
  tone?: DistributionDonutTone;   // padrão: chart-n na ordem
  description?: string;           // tooltip e aria
};

export type DistributionDonutProps = {
  items: DistributionDonutItem[];
  selectedId?: string | null;
  onSelect?: (item: DistributionDonutItem | null) => void;  // clicar no selecionado manda null
  centerValue?: string;           // padrão: total formatado (ou o valor do selecionado)
  centerLabel?: string;
  size?: number;                  // diâmetro em px; padrão 200
  thickness?: number;             // 0.1–0.5 do raio; padrão 0.28
  legendPlacement?: "side" | "below" | "none";   // padrão "side"; vira "below" abaixo de 480px de largura do container
  showPercent?: boolean;          // padrão true
  valueFormatter?: (value: number) => string;
  maxItems?: number;              // acima disso, agrupa em "Outros" (não selecionável)
  emptyMessage?: string;
  ariaLabel: string;
  labels?: Partial<{ others: string; total: string; clearSelection: string }>;
  prefix?: string;
  className?: string;
  classNames?: Partial<DistributionDonutClassNames>;
};
```

### Comportamento

- Sem `onSelect`: só leitura (fatias e itens não são botões).
- Com `onSelect`: fatias e itens da lista são botões (`aria-pressed`), acionáveis por Enter/Espaço; o não selecionado fica com opacidade reduzida quando há seleção.
- Item com valor 0 não vira fatia, mas aparece na lista com 0 quando `showPercent`.
- `aria-label` do SVG resume a distribuição; a lista é a alternativa textual.

### Testes mínimos

Arcos somam 360°; seleção e desmarcar; «Outros» com `maxItems`; teclado; vazio; claro/escuro.

---

## 2. `ResolutionStatusCell` — novo

Controle de «tratado / não tratado» de um registro: botão **Resolver**; quando resolvido, «✓ 13/11» com quem e quando e o botão **Reabrir**. Serve para tabelas, cards e rodapé de detalhe.

### Props

```ts
export type ResolutionStatus = "open" | "resolved" | "not_applicable";

export type ResolutionStatusCellLabels = {
  resolve: string;          // "Resolver"
  reopen: string;           // "Reabrir"
  resolved: string;         // "Resolvida"
  resolvedOn: string;       // "Resolvida em {date} por {user}"
  notApplicable: string;    // "Explicada"
  sending: string;          // "Salvando…"
};

export type ResolutionStatusCellProps = {
  status: ResolutionStatus;
  resolvedAt?: string | null;            // ISO
  resolvedBy?: string | null;            // nome para exibir
  onResolve?: () => void | Promise<void>;
  onReopen?: () => void | Promise<void>;
  pending?: boolean;                     // envio em andamento (controlado pelo consumidor)
  disabled?: boolean;
  variant?: "cell" | "compact" | "full"; // cell: tabela; compact: card mobile; full: rodapé de detalhe
  contextLabel?: string;                 // ex.: "NF 25655" → aria-label "Resolver NF 25655"
  dateFormatter?: (iso: string) => string;   // padrão: dd/MM no cell, dd/MM/yyyy HH:mm no full
  labels?: Partial<ResolutionStatusCellLabels>;
  prefix?: string;
  className?: string;
  classNames?: Partial<ResolutionStatusCellClassNames>;
};
```

### Comportamento

- `open` → botão «Resolver». `resolved` → «✓ data» (tooltip com «Resolvida em … por …») + botão «Reabrir». `not_applicable` → texto «Explicada», sem botão.
- Clique não propaga para a linha (`DataTableColumn.interactive: true`).
- Se `onResolve` devolve Promise, o componente mostra `sending` até resolver, mesmo sem `pending`.
- `variant="full"`: botão primário largo «Marcar como resolvida» / secundário «Reabrir», e a linha «Resolvida em … por …» visível.

### Testes mínimos

Os três estados; Promise com sucesso e com erro (volta ao estado anterior); clique não abre a linha; teclado; `aria-label` com contexto.

---

## 3. `ScopeChipBar` — evoluir

Hoje: `chips: ScopeChip[]` com `{id, label, active?, onSelect?}` (chips de escolha de escopo). Falta remover um chip e limpar todos, para servir de «filtros ativos».

### Props novas (todas opcionais)

```ts
export type ScopeChip = {
  id: string;
  label: ReactNode;
  active?: boolean;
  onSelect?: () => void;
  onRemove?: () => void;          // NOVO: mostra o "×" e remove o chip
  removeAriaLabel?: string;       // NOVO: padrão "Remover filtro {label}"
};

export type ScopeChipBarProps = {
  // …props atuais sem mudança
  onClearAll?: () => void;        // NOVO: botão "Limpar tudo" ao fim, só com 1+ chip
  clearAllLabel?: string;         // NOVO: padrão "Limpar tudo"
  emptyHint?: ReactNode;          // NOVO: texto quando chips = []
};
```

Sem as props novas: render e comportamento idênticos aos de hoje (caracterização obrigatória).

---

## 4. `SemicircleProgressGauge` — evoluir

Hoje a legenda (`legend: {id,label,count,tone}[]`) é só leitura.

### Props novas

```ts
export type SemicircleProgressGaugeProps = {
  // …props atuais sem mudança
  onLegendSelect?: (item: SemicircleProgressGaugeLegendItem) => void;  // NOVO: itens viram botões
  selectedLegendId?: string | null;                                    // NOVO: aria-pressed e destaque
  legendItemAriaLabel?: (item: SemicircleProgressGaugeLegendItem) => string; // NOVO
};
```

Sem `onLegendSelect`: legenda como hoje.

---

## 5. `HorizontalValueBars` — evoluir

Hoje: `items: {id,label,value,valueLabel?,meta?}[]`, `onItemClick`, cor única.

### Props novas

```ts
export type HorizontalValueBarItem = {
  id: string;
  label: string;
  value: number;
  valueLabel?: string;
  meta?: string;
  tone?: "default" | "success" | "warning" | "danger" | "info" | "neutral";  // NOVO; padrão "default" = cor atual
};

export type HorizontalValueBarsProps = {
  // …props atuais sem mudança
  selectedId?: string | null;                          // NOVO: destaque + aria-pressed; os demais com opacidade reduzida
  itemAriaLabel?: (item: HorizontalValueBarItem) => string;  // NOVO
};
```

Com `onItemClick`, cada barra já é acionável; a evolução garante `aria-pressed` quando `selectedId` é informado.

---

## 6. `ComparativeAreaChart` — evoluir

Hoje: `data`, `series`, `height`, `valueFormatter`, `smooth`… sem clique.

### Props novas

```ts
export type ComparativeAreaChartProps = {
  // …props atuais sem mudança
  onPointSelect?: (point: ComparativeAreaChartPoint, index: number) => void;  // NOVO: clique/Enter no ponto do eixo X
  selectedName?: string | null;                       // NOVO: faixa vertical de destaque no ponto selecionado
  pointAriaLabel?: (point: ComparativeAreaChartPoint) => string;  // NOVO: ex. "Dia 14: 6 notas; período anterior: 2"
};
```

Com `onPointSelect`, os pontos do eixo X ficam navegáveis por teclado (setas esquerda/direita, Enter seleciona). Sem a prop, o gráfico é o de hoje.

---

## Ordem de execução sugerida (E5.2 e E5.3 do planejamento)

1. Testes de caracterização dos componentes evoluídos (§3–§6) passando no código atual.
2. Evoluções §3–§6, com os testes novos.
3. Componentes novos §1–§2, com demos no catálogo.
4. Adapters `Cf*` no Portal (doc 00, regra 3).
5. Regressão: suíte do plugin-ui + build/typecheck dos consumidores de cada componente evoluído.
