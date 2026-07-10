import {
  AreaChart,
  BarChart3,
  BarChart4,
  ChartColumn,
  ChartNoAxesColumnIncreasing,
  ChartSpline,
  Circle,
  CircleDot,
  Filter,
  LineChart,
  PieChart,
  Radar,
  ScatterChart,
  type LucideIcon,
} from "lucide-react";

import {
  DELPI_CHART_CATALOG_CATEGORIES,
  DELPI_CHART_TYPE_CATALOG,
  type DelpiChartCatalogEntry,
  type DelpiChartType,
} from "./chartCatalogTypes";

const CHART_ICON_MAP: Record<string, LucideIcon> = {
  LineChart,
  AreaChart,
  BarChart3,
  BarChart4,
  ChartColumn,
  PieChart,
  CircleDot,
  ScatterChart,
  Circle,
  Radar,
  ChartSpline,
  ChartNoAxesColumnIncreasing,
  Filter,
};

export type ChartTypeCatalogPanelProps = {
  title?: string;
  onSelect: (chartType: DelpiChartType) => void;
  className?: string;
};

function ChartCatalogItem({
  entry,
  onSelect,
}: {
  entry: DelpiChartCatalogEntry;
  onSelect: (chartType: DelpiChartType) => void;
}) {
  const Icon = CHART_ICON_MAP[entry.icon] ?? BarChart3;
  return (
    <button
      type="button"
      className="delpi-ui-chart-catalog__item"
      onClick={() => onSelect(entry.type)}
      title={entry.label}
    >
      <Icon size={20} strokeWidth={1.75} aria-hidden="true" />
      <span className="delpi-ui-chart-catalog__item-label">{entry.label}</span>
    </button>
  );
}

/** Catálogo completo de tipos de gráfico (estilo PowerPoint/Excel). */
export function ChartTypeCatalogPanel({
  title = "Inserir gráfico",
  onSelect,
  className = "",
}: ChartTypeCatalogPanelProps) {
  return (
    <div className={["delpi-ui-chart-catalog", className].filter(Boolean).join(" ")} role="menu">
      <h3 className="delpi-ui-chart-catalog__title">{title}</h3>
      {DELPI_CHART_CATALOG_CATEGORIES.map((category) => {
        const items = DELPI_CHART_TYPE_CATALOG.filter((entry) => entry.category === category.id);
        if (items.length === 0) return null;
        return (
          <section key={category.id} className="delpi-ui-chart-catalog__category">
            <h4 className="delpi-ui-chart-catalog__category-label">{category.label}</h4>
            <div className="delpi-ui-chart-catalog__grid">
              {items.map((entry) => (
                <ChartCatalogItem key={entry.type} entry={entry} onSelect={onSelect} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

export { DELPI_CHART_TYPE_CATALOG, DELPI_CHART_CATALOG_CATEGORIES } from "./chartCatalogTypes";
export type { DelpiChartType, DelpiChartCatalogEntry } from "./chartCatalogTypes";
