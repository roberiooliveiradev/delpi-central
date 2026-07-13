import { ConfigurableSeriesChart, ImpactEffortMatrix, ImpactEffortMatrixLegend } from "../../components/charts";
import { ChartTypeCatalogPanel } from "../../components/charts/ChartTypeCatalogPanel";
import { TableInsertCatalogPanel } from "../../components/charts/TableInsertCatalogPanel";
import { BarSeriesChart } from "../../components/charts/BarSeriesChart";
import { LineSeriesChart } from "../../components/charts/LineSeriesChart";
import type { CatalogEntry } from "../types";

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

export const chartsCatalogEntries: CatalogEntry[] = [
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
