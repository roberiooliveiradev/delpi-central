import {
  BarChart3,
  BarChartHorizontal,
  ChartArea,
  ChartBar,
  ChartColumn,
  ChartColumnStacked,
  ChartLine,
  ChartNoAxesColumnIncreasing,
  ChartPie,
  ChartScatter,
  ChartSpline,
  Circle,
  CircleDot,
  Filter,
  Radar,
  type LucideIcon,
} from "lucide-react";

/**
 * Mapa canônico nome → Lucide para `DELPI_CHART_TYPE_CATALOG.icon`.
 * Colunas = ChartColumn (verticais); Barras = BarChartHorizontal.
 */
export const DELPI_CHART_CATALOG_ICON_MAP: Record<string, LucideIcon> = {
  ChartLine,
  ChartArea,
  ChartColumn,
  ChartBar,
  BarChartHorizontal,
  ChartColumnStacked,
  ChartNoAxesColumnIncreasing,
  ChartPie,
  CircleDot,
  ChartScatter,
  Circle,
  Radar,
  ChartSpline,
  Filter,
  /* Aliases legados (catálogo / callers antigos). */
  LineChart: ChartLine,
  AreaChart: ChartArea,
  BarChart3: ChartColumn,
  BarChart4: ChartColumnStacked,
  ChartColumnIncreasing: ChartNoAxesColumnIncreasing,
  PieChart: ChartPie,
  ScatterChart: ChartScatter,
};

export function resolveChartCatalogIcon(iconName: string | null | undefined): LucideIcon {
  if (!iconName) return BarChart3;
  return DELPI_CHART_CATALOG_ICON_MAP[iconName] ?? BarChart3;
}
