import { Columns3, RotateCcw } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";

import type { TableColumnKey } from "../utils/tableColumns";
import { TABLE_COLUMNS } from "../utils/tableColumns";

type TableColumnSettingsProps = {
  visibility: Record<TableColumnKey, boolean>;
  onToggleColumn: (key: TableColumnKey, visible: boolean) => void;
  onReset: () => void;
};

export function TableColumnSettings({
  visibility,
  onToggleColumn,
  onReset,
}: TableColumnSettingsProps) {
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

  const visibleCount = TABLE_COLUMNS.filter((column) => visibility[column.key]).length;

  return (
    <div className="pva-table-settings" ref={wrapperRef}>
      <button
        type="button"
        className="pva-btn pva-btn--ghost pva-btn--sm"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((current) => !current)}
      >
        <Columns3 size={16} aria-hidden="true" />
        Colunas
      </button>

      {open ? (
        <div id={panelId} className="pva-table-settings__panel" role="dialog" aria-label="Colunas visíveis">
          <div className="pva-table-settings__header">
            <strong>Exibir colunas</strong>
            <button type="button" className="pva-btn pva-btn--ghost pva-btn--sm" onClick={onReset}>
              <RotateCcw size={14} aria-hidden="true" />
              Restaurar
            </button>
          </div>

          <ul className="pva-check-list">
            {TABLE_COLUMNS.map((column) => {
              const checked = visibility[column.key];
              const isLastVisible = checked && visibleCount <= 1;

              return (
                <li key={column.key}>
                  <label className="pva-check-option" title={column.label}>
                    <input
                      type="checkbox"
                      checked={checked}
                      disabled={isLastVisible}
                      onChange={(event) => onToggleColumn(column.key, event.target.checked)}
                    />
                    <span className="pva-check-option__label">{column.label}</span>
                  </label>
                </li>
              );
            })}
          </ul>

          <p className="pva-table-settings__hint">
            Escolha quais colunas exibir. A preferência é salva neste navegador.
          </p>
        </div>
      ) : null}
    </div>
  );
}
