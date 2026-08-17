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
  /** Tipo atual (ex.: Alterar tipo) — destaca o item correspondente. */
  selectedType?: DelpiChartType | null;
  /** When set, only these catalog types are listed (family filter). */
  allowedTypes?: readonly DelpiChartType[] | null;
};

function ChartCatalogItem({
  entry,
  selected,
  onSelect,
}: {
  entry: DelpiChartCatalogEntry;
  selected: boolean;
  onSelect: (chartType: DelpiChartType) => void;
}) {
  const Icon = resolveChartCatalogIcon(entry.icon);
  return (
    <button
      type="button"
      className={[
        "delpi-ui-chart-catalog__item",
        selected ? "delpi-ui-chart-catalog__item--selected" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-current={selected ? "true" : undefined}
      onClick={() => onSelect(entry.type)}
      title={entry.label}
    >
      <Icon size={22} strokeWidth={1.6} aria-hidden="true" />
      <span className="delpi-ui-chart-catalog__item-label">{entry.label}</span>
    </button>
  );
}

/** Catálogo de tipos de gráfico (estilo PowerPoint/Excel). Filtrável por família. */
export function ChartTypeCatalogPanel({
  title = "Inserir gráfico",
  onSelect,
  className = "",
  selectedType = null,
  allowedTypes = null,
}: ChartTypeCatalogPanelProps) {
  const allowed =
    allowedTypes && allowedTypes.length > 0 ? new Set(allowedTypes) : null;

  const visibleCategories = DELPI_CHART_CATALOG_CATEGORIES.map((category) => {
    const items = DELPI_CHART_TYPE_CATALOG.filter((entry) => {
      if (entry.category !== category.id) return false;
      if (allowed && !allowed.has(entry.type)) return false;
      return true;
    });
    return { category, items };
  }).filter((entry) => entry.items.length > 0);

  const showCategoryLabels = visibleCategories.length > 1;

  return (
    <div className={["delpi-ui-chart-catalog", className].filter(Boolean).join(" ")} role="menu">
      <h3 className="delpi-ui-chart-catalog__title">{title}</h3>
      {visibleCategories.map(({ category, items }) => (
        <section key={category.id} className="delpi-ui-chart-catalog__category">
          {showCategoryLabels ? (
            <h4 className="delpi-ui-chart-catalog__category-label">{category.label}</h4>
          ) : null}
          <div className="delpi-ui-chart-catalog__grid">
            {items.map((entry) => (
              <ChartCatalogItem
                key={entry.type}
                entry={entry}
                selected={selectedType === entry.type}
                onSelect={onSelect}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

export { DELPI_CHART_TYPE_CATALOG, DELPI_CHART_CATALOG_CATEGORIES } from "./chartCatalogTypes";
export type { DelpiChartType, DelpiChartCatalogEntry } from "./chartCatalogTypes";
export { resolveChartCatalogIcon, DELPI_CHART_CATALOG_ICON_MAP } from "./chartCatalogIcons";
