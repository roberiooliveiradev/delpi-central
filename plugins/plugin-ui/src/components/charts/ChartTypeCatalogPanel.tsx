import {
  DELPI_CHART_CATALOG_CATEGORIES,
  DELPI_CHART_TYPE_CATALOG,
  type DelpiChartCatalogEntry,
  type DelpiChartType,
} from "./chartCatalogTypes";
import { resolveChartCatalogIcon } from "./chartCatalogIcons";

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
  const Icon = resolveChartCatalogIcon(entry.icon);
  return (
    <button
      type="button"
      className="delpi-ui-chart-catalog__item"
      onClick={() => onSelect(entry.type)}
      title={entry.label}
    >
      <Icon size={22} strokeWidth={1.6} aria-hidden="true" />
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
export { resolveChartCatalogIcon, DELPI_CHART_CATALOG_ICON_MAP } from "./chartCatalogIcons";
