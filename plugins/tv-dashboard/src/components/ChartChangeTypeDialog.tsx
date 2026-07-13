import { useEffect, useMemo, useState } from "react";
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
  type DelpiChartType,
} from "@delpi/plugin-ui/index";

import { Modal } from "./ui/Modal";

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

type CatalogCategoryId = (typeof DELPI_CHART_CATALOG_CATEGORIES)[number]["id"];

type Props = {
  open: boolean;
  currentType: DelpiChartType;
  onClose: () => void;
  onConfirm: (chartType: DelpiChartType) => void;
};

/**
 * Diálogo «Alterar Tipo de Gráfico» — sidebar de categorias + grade + preview + OK/Cancelar.
 * Mesmo catálogo de Inserir (`DELPI_CHART_TYPE_CATALOG`).
 */
export function ChartChangeTypeDialog({ open, currentType, onClose, onConfirm }: Props) {
  const initialCategory = (DELPI_CHART_TYPE_CATALOG.find((item) => item.type === currentType)
    ?.category ?? "series") as CatalogCategoryId;
  const [categoryId, setCategoryId] = useState<CatalogCategoryId>(initialCategory);
  const [draftType, setDraftType] = useState<DelpiChartType>(currentType);

  useEffect(() => {
    if (!open) return;
    setDraftType(currentType);
    setCategoryId(
      (DELPI_CHART_TYPE_CATALOG.find((item) => item.type === currentType)?.category ??
        "series") as CatalogCategoryId,
    );
  }, [open, currentType]);

  const items = useMemo(
    () => DELPI_CHART_TYPE_CATALOG.filter((entry) => entry.category === categoryId),
    [categoryId],
  );
  const draftEntry = DELPI_CHART_TYPE_CATALOG.find((entry) => entry.type === draftType);
  const DraftIcon = draftEntry ? (CHART_ICON_MAP[draftEntry.icon] ?? BarChart3) : BarChart3;

  return (
    <Modal
      open={open}
      title="Alterar tipo de gráfico"
      onClose={onClose}
      className="td-modal--wide td-modal--chart-type"
    >
      <div className="td-chart-type-dialog">
        <aside className="td-chart-type-dialog__nav" aria-label="Categorias">
          {DELPI_CHART_CATALOG_CATEGORIES.map((category) => (
            <button
              key={category.id}
              type="button"
              className={[
                "td-chart-type-dialog__nav-item",
                categoryId === category.id ? "td-chart-type-dialog__nav-item--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => setCategoryId(category.id)}
            >
              {category.label}
            </button>
          ))}
        </aside>

        <div className="td-chart-type-dialog__main">
          <div className="td-chart-type-dialog__grid" role="listbox" aria-label="Tipos de gráfico">
            {items.map((entry) => {
              const Icon = CHART_ICON_MAP[entry.icon] ?? BarChart3;
              const active = draftType === entry.type;
              return (
                <button
                  key={entry.type}
                  type="button"
                  role="option"
                  aria-selected={active}
                  className={[
                    "td-chart-type-dialog__item",
                    active ? "td-chart-type-dialog__item--active" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={() => setDraftType(entry.type)}
                  onDoubleClick={() => onConfirm(entry.type)}
                  title={entry.label}
                >
                  <Icon size={22} strokeWidth={1.75} aria-hidden="true" />
                  <span>{entry.label}</span>
                </button>
              );
            })}
          </div>

          <div className="td-chart-type-dialog__preview" aria-live="polite">
            <DraftIcon size={48} strokeWidth={1.5} aria-hidden="true" />
            <p>{draftEntry?.label ?? draftType}</p>
          </div>
        </div>
      </div>

      <div className="td-chart-type-dialog__footer td-modal-actions--end">
        <button type="button" className="td-btn td-btn--ghost" onClick={onClose}>
          Cancelar
        </button>
        <button
          type="button"
          className="td-btn td-btn--primary"
          onClick={() => onConfirm(draftType)}
        >
          OK
        </button>
      </div>
    </Modal>
  );
}
