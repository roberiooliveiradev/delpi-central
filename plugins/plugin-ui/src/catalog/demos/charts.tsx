import { useState } from "react";

import { PUC_PREFIX } from "../../app/bemPrefix";
import {
  ComparativeAreaChart,
  ConfigurableSeriesChart,
  DistributionDonut,
  HorizontalValueBars,
  ImpactEffortMatrix,
  ImpactEffortMatrixLegend,
  type DistributionDonutItem,
} from "../../components/charts";
import { SemicircleProgressGauge } from "../../components/charts/SemicircleProgressGauge";
import { ChartTypeCatalogPanel } from "../../components/charts/ChartTypeCatalogPanel";
import { TableInsertCatalogPanel } from "../../components/charts/TableInsertCatalogPanel";
import { BarSeriesChart } from "../../components/charts/BarSeriesChart";
import { LineSeriesChart } from "../../components/charts/LineSeriesChart";
import type { CatalogEntryDraft } from "../types";

const SERIES_POINTS = [
  { label: "Jan", value: 12 },
  { label: "Fev", value: 18 },
  { label: "Mar", value: 15 },
  { label: "Abr", value: 22 },
];

const MATRIX_POINTS = [
  { id: "1", label: "Rápido", impacto: 80, esforco: 20, quadrante: "quick_win" as const },
  { id: "2", label: "Estratégico", impacto: 85, esforco: 75, quadrante: "strategic" as const },
  { id: "3", label: "Complementar", impacto: 30, esforco: 25, quadrante: "fill_in" as const },
  { id: "4", label: "Reavaliar", impacto: 25, esforco: 80, quadrante: "rethink" as const },
];

const DONUT_ITEMS: DistributionDonutItem[] = [
  { id: "t1", label: "Tema A", value: 42, description: "Maior concentração" },
  { id: "t2", label: "Tema B", value: 27 },
  { id: "t3", label: "Tema C", value: 18 },
  { id: "t4", label: "Tema D", value: 9 },
  { id: "t5", label: "Tema E", value: 4 },
  { id: "t6", label: "Tema F", value: 0 },
];

const BAR_ITEMS = [
  { id: "a", label: "Grupo Alfa", value: 38, meta: "12 itens", tone: "danger" as const },
  { id: "b", label: "Grupo Beta", value: 24, meta: "8 itens", tone: "warning" as const },
  { id: "c", label: "Grupo Gama", value: 15, meta: "5 itens", tone: "info" as const },
  { id: "d", label: "Grupo Delta", value: 6, meta: "2 itens" },
];

const AREA_DATA = [
  { name: "10", atual: 3, anterior: 1 },
  { name: "11", atual: 6, anterior: 2 },
  { name: "12", atual: 4, anterior: 5 },
  { name: "13", atual: 8, anterior: 3 },
  { name: "14", atual: 5, anterior: 4 },
];

const AREA_SERIES = [
  { dataKey: "atual", name: "Período atual", color: "var(--chart-1, #089bdb)" },
  { dataKey: "anterior", name: "Período anterior", color: "var(--chart-2, #003866)", fillOpacity: 0.2 },
];

function SelectableLegendGaugeDemo() {
  const [selected, setSelected] = useState<string | null>(null);
  return (
    <SemicircleProgressGauge
      prefix={PUC_PREFIX}
      value={82}
      centerLabel="dentro do esperado"
      selectedLegendId={selected}
      onLegendSelect={(item) => setSelected((current) => (current === item.id ? null : item.id))}
      legendItemAriaLabel={(item) => `Filtrar por ${item.label}: ${item.count}`}
      legend={[
        { id: "ok", label: "Conforme", count: 41, tone: "success" },
        { id: "warn", label: "Atenção", count: 9, tone: "warning" },
        { id: "bad", label: "Crítico", count: 3, tone: "danger" },
      ]}
    />
  );
}

function SelectableBarsDemo() {
  const [selected, setSelected] = useState<string | null>("b");
  return (
    <HorizontalValueBars
      prefix={PUC_PREFIX}
      aria-label="Ranking por grupo"
      layout="stacked"
      items={BAR_ITEMS}
      selectedId={selected}
      onItemClick={(item) => setSelected((current) => (current === item.id ? null : item.id))}
      itemAriaLabel={(item) => `Filtrar por ${item.label}`}
    />
  );
}

function SelectableAreaDemo() {
  const [selected, setSelected] = useState<string | null>("13");
  return (
    <div className="puc-sandbox-chart">
      <ComparativeAreaChart
        prefix={PUC_PREFIX}
        data={AREA_DATA}
        series={AREA_SERIES}
        valueFormatter={(value) => String(value)}
        yAxisWidth={32}
        selectedName={selected}
        onPointSelect={(point) => setSelected(String(point.name))}
        pointAriaLabel={(point) => `Dia ${point.name}: ${point.atual} no período; anterior: ${point.anterior}`}
      />
    </div>
  );
}

function SelectableDonutDemo({ maxItems }: { maxItems?: number }) {
  const [selected, setSelected] = useState<string | null>(null);
  return (
    <DistributionDonut
      prefix={PUC_PREFIX}
      ariaLabel="Distribuição por tema"
      items={DONUT_ITEMS}
      maxItems={maxItems}
      selectedId={selected}
      onSelect={(item) => setSelected(item?.id ?? null)}
    />
  );
}

export const chartsCatalogEntries: CatalogEntryDraft[] = [
  {
    id: "charts.ConfigurableSeriesChart",
    family: "charts",
    exportName: "ConfigurableSeriesChart",
    title: "ConfigurableSeriesChart",
    description: "Gráfico de série SVG nativo (line/bar/…).",
    demos: [
      {
        id: "line",
        label: "Linha",
        render: () => (
          <div className="puc-sandbox-chart">
            <ConfigurableSeriesChart
              chartType="line"
              points={SERIES_POINTS}
              options={{ title: "Série demo", showLegend: false }}
            />
          </div>
        ),
      },
    ],
  },
  {
    id: "charts.LineSeriesChart",
    family: "charts",
    exportName: "LineSeriesChart",
    title: "LineSeriesChart",
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <div className="puc-sandbox-chart">
            <LineSeriesChart points={SERIES_POINTS} options={{ title: "Linha" }} />
          </div>
        ),
      },
    ],
  },
  {
    id: "charts.BarSeriesChart",
    family: "charts",
    exportName: "BarSeriesChart",
    title: "BarSeriesChart",
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <div className="puc-sandbox-chart">
            <BarSeriesChart points={SERIES_POINTS} options={{ title: "Barras" }} />
          </div>
        ),
      },
    ],
  },
  {
    id: "charts.ImpactEffortMatrix",
    family: "charts",
    exportName: "ImpactEffortMatrix",
    title: "ImpactEffortMatrix",
    demos: [
      {
        id: "default",
        label: "Scatter",
        render: () => (
          <div className="puc-sandbox-chart">
            <ImpactEffortMatrix points={MATRIX_POINTS} />
          </div>
        ),
      },
    ],
  },
  {
    id: "charts.ImpactEffortMatrixLegend",
    family: "charts",
    exportName: "ImpactEffortMatrixLegend",
    title: "ImpactEffortMatrixLegend",
    demos: [
      {
        id: "default",
        label: "Legenda",
        render: () => <ImpactEffortMatrixLegend />,
      },
    ],
  },
  {
    id: "charts.SemicircleProgressGauge",
    family: "charts",
    exportName: "SemicircleProgressGauge",
    title: "SemicircleProgressGauge",
    demos: [
      {
        id: "default",
        label: "Com legenda",
        render: () => (
          <SemicircleProgressGauge
            prefix="puc"
            value={82}
            centerLabel="dentro do esperado"
            legend={[
              { id: "ok", label: "Conforme", count: 41, tone: "success" },
              { id: "warn", label: "Atenção", count: 9, tone: "warning" },
            ]}
          />
        ),
      },
      {
        id: "empty",
        label: "Zero",
        render: () => <SemicircleProgressGauge prefix="puc" value={0} centerLabel="sem itens" />,
      },
      {
        id: "selectable",
        label: "Legenda selecionável",
        render: () => <SelectableLegendGaugeDemo />,
      },
    ],
  },
  {
    id: "charts.HorizontalValueBars",
    family: "charts",
    exportName: "HorizontalValueBars",
    title: "HorizontalValueBars",
    description: "Barras horizontais de ranking; tom por item e seleção opcionais.",
    propsSummary: ["items", "onItemClick", "selectedId", "itemAriaLabel", "layout"],
    demos: [
      {
        id: "default",
        label: "Somente leitura",
        render: () => (
          <HorizontalValueBars
            prefix={PUC_PREFIX}
            aria-label="Ranking"
            items={[
              { id: "a", label: "Grupo Alfa", value: 38, meta: "12 itens" },
              { id: "b", label: "Grupo Beta", value: 24, meta: "8 itens" },
            ]}
          />
        ),
      },
      {
        id: "tone-selection",
        label: "Tons e seleção",
        render: () => <SelectableBarsDemo />,
      },
    ],
  },
  {
    id: "charts.ComparativeAreaChart",
    family: "charts",
    exportName: "ComparativeAreaChart",
    title: "ComparativeAreaChart",
    description: "Área comparativa com tema claro/escuro; ponto do eixo X selecionável.",
    propsSummary: ["data", "series", "onPointSelect", "selectedName", "pointAriaLabel"],
    demos: [
      {
        id: "default",
        label: "Somente leitura",
        render: () => (
          <div className="puc-sandbox-chart">
            <ComparativeAreaChart
              prefix={PUC_PREFIX}
              data={AREA_DATA}
              series={AREA_SERIES}
              valueFormatter={(value) => String(value)}
              yAxisWidth={32}
            />
          </div>
        ),
      },
      {
        id: "selectable",
        label: "Ponto selecionável (setas + Enter)",
        render: () => <SelectableAreaDemo />,
      },
    ],
  },
  {
    id: "charts.DistributionDonut",
    family: "charts",
    exportName: "DistributionDonut",
    title: "DistributionDonut",
    description:
      "Rosca de distribuição com lista ao lado; fatias e itens filtram (aria-pressed). Reusa a geometria de ChartSeriesPie.",
    propsSummary: ["items", "selectedId", "onSelect", "maxItems", "legendPlacement", "ariaLabel"],
    demos: [
      {
        id: "readonly",
        label: "Somente leitura",
        render: () => (
          <DistributionDonut prefix={PUC_PREFIX} ariaLabel="Distribuição por tema" items={DONUT_ITEMS} />
        ),
      },
      {
        id: "selectable",
        label: "Selecionável",
        render: () => <SelectableDonutDemo />,
      },
      {
        id: "others",
        label: "Outros (maxItems=3)",
        render: () => <SelectableDonutDemo maxItems={3} />,
      },
      {
        id: "below",
        label: "Legenda abaixo",
        render: () => (
          <DistributionDonut
            prefix={PUC_PREFIX}
            ariaLabel="Distribuição por tema"
            items={DONUT_ITEMS}
            legendPlacement="below"
            size={160}
          />
        ),
      },
      {
        id: "empty",
        label: "Vazio",
        render: () => (
          <DistributionDonut prefix={PUC_PREFIX} ariaLabel="Distribuição" items={[]} emptyMessage="Sem ocorrências." />
        ),
      },
    ],
  },
  {
    id: "charts.ChartTypeCatalogPanel",
    family: "charts",
    exportName: "ChartTypeCatalogPanel",
    title: "ChartTypeCatalogPanel",
    demos: [
      {
        id: "default",
        label: "Catálogo",
        render: () => (
          <ChartTypeCatalogPanel onSelect={() => undefined} />
        ),
      },
    ],
  },
  {
    id: "charts.TableInsertCatalogPanel",
    family: "charts",
    exportName: "TableInsertCatalogPanel",
    title: "TableInsertCatalogPanel",
    demos: [
      {
        id: "default",
        label: "Inserir tabela",
        render: () => <TableInsertCatalogPanel onSelect={() => undefined} />,
      },
    ],
  },
];
