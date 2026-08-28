import { Columns3, GripVertical, RotateCcw } from "lucide-react";
import { useEffect, useId, useRef, useState, type DragEvent } from "react";

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
  /** Aria do handle de arrastar (default: «Reordenar coluna …»). */
  reorderAriaLabel?: (columnLabel: string) => string;
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
  /** Habilita arrastar para reordenar (default true quando `onReorderColumns` existe). */
  enableReorder?: boolean;
  /** Troca a posição de `fromKey` com a de `toKey` no catálogo. */
  onReorderColumns?: (fromKey: string, toKey: string) => void;
};

/**
 * Menu “Colunas” da toolbar de tabela — painel com checkboxes de visibilidade
 * e reordenação por drag-and-drop.
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
  enableReorder,
  onReorderColumns,
}: TableColumnVisibilityMenuProps) {
  const [open, setOpen] = useState(false);
  const [dragKey, setDragKey] = useState<string | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const panelId = useId();
  const canReorder = Boolean(onReorderColumns) && enableReorder !== false;

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

  const onDragStart = (event: DragEvent<HTMLElement>, key: string) => {
    if (!canReorder || !onReorderColumns) return;
    setDragKey(key);
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", key);
  };

  const onDragOver = (event: DragEvent<HTMLElement>) => {
    if (!canReorder) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  };

  const onDrop = (event: DragEvent<HTMLElement>, targetKey: string) => {
    if (!canReorder || !onReorderColumns) return;
    event.preventDefault();
    const fromKey = dragKey || event.dataTransfer.getData("text/plain");
    setDragKey(null);
    if (!fromKey || fromKey === targetKey) return;
    onReorderColumns(fromKey, targetKey);
  };

  return (
    <div className={rootClass} ref={wrapperRef}>
      <button
        type="button"
        className="delpi-ui-table-toolbar-action delpi-ui-table-columns__trigger"
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
            <button
              type="button"
              className="delpi-ui-table-toolbar-action delpi-ui-table-columns__reset"
              onClick={onReset}
            >
              <RotateCcw size={14} aria-hidden="true" />
              {labels.reset}
            </button>
          </div>

          <ul className="delpi-ui-table-columns__list">
            {columns.map((column) => {
              const checked = Boolean(visibility[column.key]);
              const isLastVisible = keepAtLeastOne && checked && visibleCount <= 1;
              const isDragging = dragKey === column.key;

              return (
                <li
                  key={column.key}
                  className={[
                    "delpi-ui-table-columns__item",
                    isDragging ? "delpi-ui-table-columns__item--dragging" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  draggable={canReorder}
                  onDragStart={(event) => onDragStart(event, column.key)}
                  onDragOver={onDragOver}
                  onDrop={(event) => onDrop(event, column.key)}
                  onDragEnd={() => setDragKey(null)}
                >
                  {canReorder ? (
                    <span
                      className="delpi-ui-table-columns__drag-handle"
                      aria-label={
                        labels.reorderAriaLabel?.(column.label) ??
                        `Reordenar coluna ${column.label}`
                      }
                      title="Arrastar para reordenar"
                    >
                      <GripVertical size={14} aria-hidden="true" />
                    </span>
                  ) : null}
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
