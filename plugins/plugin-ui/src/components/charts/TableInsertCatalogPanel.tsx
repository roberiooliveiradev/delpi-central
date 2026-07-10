import { useState } from "react";

import {
  DELPI_TABLE_GRID_MAX_COLS,
  DELPI_TABLE_GRID_MAX_ROWS,
  DELPI_TABLE_INSERT_PRESETS,
  type DelpiTableInsertPreset,
  type DelpiTableInsertSelection,
} from "./chartCatalogTypes";

export type TableInsertCatalogPanelProps = {
  title?: string;
  onSelect: (selection: DelpiTableInsertSelection) => void;
  className?: string;
};

/** Seletor de grade (estilo Excel) + presets de tabela. */
export function TableInsertCatalogPanel({
  title = "Inserir tabela",
  onSelect,
  className = "",
}: TableInsertCatalogPanelProps) {
  const [hoverRows, setHoverRows] = useState(0);
  const [hoverCols, setHoverCols] = useState(0);

  function handleCellHover(row: number, col: number) {
    setHoverRows(row);
    setHoverCols(col);
  }

  function handleCellClick(row: number, col: number, preset: DelpiTableInsertPreset = "grid") {
    onSelect({ rows: row, cols: col, preset });
    setHoverRows(0);
    setHoverCols(0);
  }

  function handleGridLeave() {
    setHoverRows(0);
    setHoverCols(0);
  }

  const sizeLabel =
    hoverRows > 0 && hoverCols > 0 ? `${hoverCols} × ${hoverRows}` : "Passe o mouse na grade";

  return (
    <div className={["delpi-ui-table-insert-catalog", className].filter(Boolean).join(" ")} role="menu">
      <h3 className="delpi-ui-table-insert-catalog__title">{title}</h3>
      <p className="delpi-ui-table-insert-catalog__hint">Escolha o tamanho ou um estilo pronto.</p>

      <div className="delpi-ui-table-insert-catalog__grid-wrap">
        <div
          className="delpi-ui-table-insert-catalog__grid"
          style={{ gridTemplateColumns: `repeat(${DELPI_TABLE_GRID_MAX_COLS}, 18px)` }}
          onMouseLeave={handleGridLeave}
          role="presentation"
        >
          {Array.from({ length: DELPI_TABLE_GRID_MAX_ROWS }, (_, rowIndex) => {
            const row = rowIndex + 1;
            return Array.from({ length: DELPI_TABLE_GRID_MAX_COLS }, (_, colIndex) => {
              const col = colIndex + 1;
              const active = row <= hoverRows && col <= hoverCols;
              return (
                <button
                  key={`${row}-${col}`}
                  type="button"
                  className={[
                    "delpi-ui-table-insert-catalog__cell",
                    active ? "delpi-ui-table-insert-catalog__cell--active" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  aria-label={`${col} colunas por ${row} linhas`}
                  onMouseEnter={() => handleCellHover(row, col)}
                  onClick={() => handleCellClick(row, col)}
                />
              );
            });
          })}
        </div>
        <span className="delpi-ui-table-insert-catalog__size-label">{sizeLabel}</span>
      </div>

      <div className="delpi-ui-table-insert-catalog__presets">
        {DELPI_TABLE_INSERT_PRESETS.map((preset) => (
          <button
            key={preset.id}
            type="button"
            className="delpi-ui-table-insert-catalog__preset"
            onClick={() => handleCellClick(4, 3, preset.id)}
          >
            <span className="delpi-ui-table-insert-catalog__preset-label">{preset.label}</span>
            <span className="delpi-ui-table-insert-catalog__preset-hint">{preset.hint}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export {
  DELPI_TABLE_GRID_MAX_COLS,
  DELPI_TABLE_GRID_MAX_ROWS,
  DELPI_TABLE_INSERT_PRESETS,
} from "./chartCatalogTypes";
export type { DelpiTableInsertPreset, DelpiTableInsertSelection } from "./chartCatalogTypes";
