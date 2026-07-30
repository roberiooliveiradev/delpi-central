import { useEffect, useMemo, useState } from "react";
import {
  DELPI_CHART_CATALOG_CATEGORIES,
  DELPI_CHART_TYPE_CATALOG,
  resolveChartCatalogIcon,
  type DelpiChartType,
} from "@delpi/plugin-ui/index";

import { HostContainedDialog } from "./ui/Modal";

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
  const DraftIcon = resolveChartCatalogIcon(draftEntry?.icon);
  const categoryLabel =
    DELPI_CHART_CATALOG_CATEGORIES.find((category) => category.id === categoryId)?.label ?? "";

  const selectCategory = (nextId: CatalogCategoryId) => {
    setCategoryId(nextId);
    const inCategory = DELPI_CHART_TYPE_CATALOG.some(
      (entry) => entry.category === nextId && entry.type === draftType,
    );
    if (!inCategory) {
      const first = DELPI_CHART_TYPE_CATALOG.find((entry) => entry.category === nextId);
      if (first) setDraftType(first.type);
    }
  };

  return (
    <HostContainedDialog
      open={open}
      title="Alterar tipo de gráfico"
      onClose={onClose}
      className="td-modal--wide td-modal--chart-type"
      footer={
        <div className="td-modal-actions td-modal-actions--end">
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
      }
    >
      <div className="td-chart-type-dialog">
        <aside className="td-chart-type-dialog__nav" aria-label="Categorias">
          <p className="td-chart-type-dialog__nav-label">Categorias</p>
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
              onClick={() => selectCategory(category.id)}
            >
              {category.label}
            </button>
          ))}
        </aside>

        <div className="td-chart-type-dialog__main">
          <header className="td-chart-type-dialog__heading">
            <h3 className="td-chart-type-dialog__heading-title">{categoryLabel}</h3>
            <p className="td-chart-type-dialog__heading-hint">
              Escolha o tipo · clique duplo confirma
            </p>
          </header>

          <div className="td-chart-type-dialog__grid" role="listbox" aria-label="Tipos de gráfico">
            {items.map((entry) => {
              const Icon = resolveChartCatalogIcon(entry.icon);
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
                  <span className="td-chart-type-dialog__item-icon" aria-hidden="true">
                    <Icon size={28} strokeWidth={1.5} />
                  </span>
                  <span className="td-chart-type-dialog__item-label">{entry.label}</span>
                </button>
              );
            })}
          </div>

          <div className="td-chart-type-dialog__preview" aria-live="polite">
            <span className="td-chart-type-dialog__preview-icon" aria-hidden="true">
              <DraftIcon size={36} strokeWidth={1.5} />
            </span>
            <div className="td-chart-type-dialog__preview-copy">
              <p className="td-chart-type-dialog__preview-eyebrow">Selecionado</p>
              <p className="td-chart-type-dialog__preview-title">
                {draftEntry?.label ?? draftType}
              </p>
            </div>
          </div>
        </div>
      </div>
    </HostContainedDialog>
  );
}
