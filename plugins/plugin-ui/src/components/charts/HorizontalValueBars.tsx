import { useMemo, type ReactNode } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type HorizontalValueBarTone =
  | "default"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "neutral";

export type HorizontalValueBarItem = {
  id: string;
  label: string;
  value: number;
  /** Texto à direita (default: valor formatado). */
  valueLabel?: string;
  meta?: string;
  /** Fill color family. Default `"default"` keeps the current accent gradient. */
  tone?: HorizontalValueBarTone;
};

export type HorizontalValueBarsClassNames = {
  root: string;
  empty: string;
  list: string;
  row: string;
  rowButton: string;
  label: string;
  meta: string;
  track: string;
  fill: string;
  value: string;
};

export type HorizontalValueBarsProps = {
  items: HorizontalValueBarItem[];
  emptyMessage?: string;
  /** Override do máximo da barra (default = max dos valores). */
  max?: number;
  formatValue?: (value: number) => string;
  onItemClick?: (item: HorizontalValueBarItem) => void;
  className?: string;
  classNames?: Partial<HorizontalValueBarsClassNames>;
  prefix?: string;
  "aria-label"?: string;
  leading?: ReactNode;
  /**
   * `columns` (padrão — rótulo | barra | valor na mesma linha) ou
   * `stacked` (rótulo + valor no topo, barra em largura plena abaixo),
   * indicado para rótulos longos em rankings gerenciais.
   */
  layout?: "columns" | "stacked";
  /**
   * Highlights one item (and dims the others). When provided (even as `null`)
   * clickable rows expose `aria-pressed`.
   */
  selectedId?: string | null;
  /** Accessible name of a row (button when clickable, list item otherwise). */
  itemAriaLabel?: (item: HorizontalValueBarItem) => string;
};

export function horizontalValueBarsBemClasses(prefix: string): HorizontalValueBarsClassNames {
  const ui = "delpi-ui-horizontal-value-bars";
  return {
    root: delpiUiClass(`${prefix}-horizontal-value-bars`, ui),
    empty: delpiUiClass(`${prefix}-horizontal-value-bars__empty`, `${ui}__empty`),
    list: delpiUiClass(`${prefix}-horizontal-value-bars__list`, `${ui}__list`),
    row: delpiUiClass(`${prefix}-horizontal-value-bars__row`, `${ui}__row`),
    rowButton: delpiUiClass(`${prefix}-horizontal-value-bars__row-button`, `${ui}__row-button`),
    label: delpiUiClass(`${prefix}-horizontal-value-bars__label`, `${ui}__label`),
    meta: delpiUiClass(`${prefix}-horizontal-value-bars__meta`, `${ui}__meta`),
    track: delpiUiClass(`${prefix}-horizontal-value-bars__track`, `${ui}__track`),
    fill: delpiUiClass(`${prefix}-horizontal-value-bars__fill`, `${ui}__fill`),
    value: delpiUiClass(`${prefix}-horizontal-value-bars__value`, `${ui}__value`),
  };
}

function defaultFormat(value: number): string {
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
}

/** Lista de barras horizontais (ranking / top N) — CSS + tokens do kit. */
export function HorizontalValueBars({
  items,
  emptyMessage = "Sem dados.",
  max,
  formatValue = defaultFormat,
  onItemClick,
  className,
  classNames: classNamesOverride,
  prefix = "ds",
  "aria-label": ariaLabel,
  layout = "columns",
  selectedId,
  itemAriaLabel,
}: HorizontalValueBarsProps) {
  const base = useMemo(() => horizontalValueBarsBemClasses(prefix), [prefix]);
  const classNames = { ...base, ...classNamesOverride };
  const peak = max ?? Math.max(0, ...items.map((item) => item.value));
  const denom = peak > 0 ? peak : 1;
  const selectionActive = selectedId !== undefined;

  if (items.length === 0) {
    return (
      <div className={[classNames.root, className].filter(Boolean).join(" ")}>
        <p className={classNames.empty}>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div
      className={[
        classNames.root,
        layout === "stacked" ? `${classNames.root}--stacked` : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      data-layout={layout}
      role="list"
      aria-label={ariaLabel}
    >
      <ul className={classNames.list}>
        {items.map((item, index) => {
          const widthPct = Math.min(100, Math.max(0, (item.value / denom) * 100));
          const tone = item.tone && item.tone !== "default" ? item.tone : null;
          const isSelected = selectedId != null && selectedId === item.id;
          const isDimmed = selectedId != null && selectedId !== item.id;
          const fillClass = tone
            ? withBemModifier(classNames.fill, `tone-${tone}`)
            : classNames.fill;
          const rowBase = classNames.row;
          const rowClass = isSelected
            ? withBemModifier(rowBase, "selected")
            : isDimmed
              ? withBemModifier(rowBase, "dimmed")
              : rowBase;
          const rowState = {
            "data-selected": isSelected ? "true" : undefined,
            "data-dimmed": isDimmed ? "true" : undefined,
          };
          const ariaLabelForItem = itemAriaLabel?.(item);
          const body = (
            <>
              <div className={classNames.label}>
                <span>{item.label}</span>
                {item.meta ? <span className={classNames.meta}>{item.meta}</span> : null}
              </div>
              <div className={classNames.track} aria-hidden="true">
                <span className={fillClass} style={{ width: `${widthPct}%` }} />
              </div>
              <span className={classNames.value}>
                {item.valueLabel ?? formatValue(item.value)}
              </span>
            </>
          );
          if (onItemClick) {
            return (
              <li
                key={item.id}
                className={rowClass}
                role="listitem"
                data-rank={index + 1}
                {...rowState}
              >
                <button
                  type="button"
                  className={classNames.rowButton}
                  aria-pressed={selectionActive ? isSelected : undefined}
                  aria-label={ariaLabelForItem}
                  onClick={() => onItemClick(item)}
                >
                  {body}
                </button>
              </li>
            );
          }
          return (
            <li
              key={item.id}
              className={rowClass}
              role="listitem"
              data-rank={index + 1}
              aria-label={ariaLabelForItem}
              {...rowState}
            >
              {body}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
