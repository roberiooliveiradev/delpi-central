import { Columns3, RotateCcw } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";

import { NativeCheckboxControl } from "../forms/NativeCheckboxControl";

export type TableColumnVisibilityItem = {
  key: string;
  label: string;
};

export type TableColumnVisibilityMenuLabels = {
  trigger: string;
  panelTitle: string;
  reset: string;
  hint: string;
  columnAriaLabel: (columnLabel: string) => string;
  panelAriaLabel?: string;
};

export type TableColumnVisibilityMenuProps = {
  columns: readonly TableColumnVisibilityItem[];
  visibility: Record<string, boolean>;
  onToggleColumn: (key: string, visible: boolean) => void;
  onReset: () => void;
  labels: TableColumnVisibilityMenuLabels;
  className?: string;
  /** Impede desmarcar a última coluna visível (default true). */
  keepAtLeastOne?: boolean;
};

/**
 * Menu “Colunas” da toolbar de tabela — painel com checkboxes de visibilidade.
 * CSS: `styles/table-column-visibility.css` (`.delpi-ui-table-columns*`).
 */
export function TableColumnVisibilityMenu({
  columns,
  visibility,
  onToggleColumn,
  onReset,
  labels,
  className,
  keepAtLeastOne = true,
}: TableColumnVisibilityMenuProps) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const panelId = useId();

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current?.contains(event.target as Node)) return;
      setOpen(false);
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const visibleCount = columns.filter((column) => visibility[column.key]).length;
  const rootClass = ["delpi-ui-table-columns", className].filter(Boolean).join(" ");

  return (
    <div className={rootClass} ref={wrapperRef}>
      <button
        type="button"
        className="delpi-ui-table-columns__trigger"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((current) => !current)}
      >
        <Columns3 size={16} aria-hidden="true" />
        {labels.trigger}
      </button>

      {open ? (
        <div
          id={panelId}
          className="delpi-ui-table-columns__panel"
          role="dialog"
          aria-label={labels.panelAriaLabel ?? labels.trigger}
        >
          <div className="delpi-ui-table-columns__header">
            <strong className="delpi-ui-table-columns__title">{labels.panelTitle}</strong>
            <button type="button" className="delpi-ui-table-columns__reset" onClick={onReset}>
              <RotateCcw size={14} aria-hidden="true" />
              {labels.reset}
            </button>
          </div>

          <ul className="delpi-ui-table-columns__list">
            {columns.map((column) => {
              const checked = Boolean(visibility[column.key]);
              const isLastVisible = keepAtLeastOne && checked && visibleCount <= 1;

              return (
                <li key={column.key}>
                  <NativeCheckboxControl
                    className="delpi-ui-table-columns__option"
                    checked={checked}
                    disabled={isLastVisible}
                    onChange={(visible) => onToggleColumn(column.key, visible)}
                    aria-label={labels.columnAriaLabel(column.label)}
                    label={column.label}
                  />
                </li>
              );
            })}
          </ul>

          <p className="delpi-ui-table-columns__hint">{labels.hint}</p>
        </div>
      ) : null}
    </div>
  );
}
